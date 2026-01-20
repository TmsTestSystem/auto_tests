"""
Построение отчёта по времени выполнения компонентов на основе jobs_from_responses.csv
и /api/events/{job_uuid}.

Использование:
  python build_component_timings.py --report-dir path/to/report_dir

где report_dir содержит jobs_from_responses.csv (созданный Locust'ом).
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import urllib3

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.project_process_log import ProjectProcessLogAPI  # type: ignore  # noqa: E402


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_TITLE_TEST_SUFFIX_RE = re.compile(r"^(?P<base>.*?)(?:_test(?P<level>[1-9]\d*))$", re.IGNORECASE)


def parse_component_title_hierarchy(title: str) -> Dict[str, Any]:
    """
    Примитивная иерархия по суффиксам:
    - *_test1 -> level=1
    - *_test2 -> level=2 (вложено в test1)
    - *_test3 -> level=3 (вложено в test2)

    Возвращает:
    - title_raw: исходное имя
    - title_base: имя без _testN
    - title_level: int | None
    - title_path: человекочитаемый путь (например: "test1 / test2 / Timer")
    """
    t = title or ""
    m = _TITLE_TEST_SUFFIX_RE.match(t)
    if not m:
        return {
            "title_raw": t,
            "title_base": t,
            "title_level": None,
            "title_path": t,
        }
    base = (m.group("base") or "").strip()
    level_s = m.group("level")
    level = int(level_s) if level_s else None

    # для читаемости: level -> "testN / <base>"
    if level is None:
        path = base
    else:
        path = f"test{level} / {base}"

    return {
        "title_raw": t,
        "title_base": base,
        "title_level": level,
        "title_path": path,
    }


def load_jobs_from_responses_csv(path: Path) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"jobs_from_responses.csv не найден: {path}")
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)
    return jobs


def _to_int_us(value: Any) -> Optional[int]:
    """
    inserted_timestamp приходит как float (микросекунды от epoch).
    Приводим к int microseconds.
    """
    try:
        if value is None:
            return None
        return int(float(value))
    except Exception:
        return None


def _extract_events(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        ev = payload.get("events")
        if isinstance(ev, list):
            return [e for e in ev if isinstance(e, dict)]
        if isinstance(ev, dict) and "items" in ev and isinstance(ev["items"], list):
            return [e for e in ev["items"] if isinstance(e, dict)]
    if isinstance(payload, list):
        return [e for e in payload if isinstance(e, dict)]
    return []


def _compute_component_rows(events: List[Dict[str, Any]]) -> List[Tuple[str, str, str, int, int, float]]:
    """
    Возвращает список (component_key, title, component_type, start_us, end_us, duration_ms)
    для всех component_event.
    """
    by_key: Dict[str, Dict[str, Any]] = {}
    for e in events:
        if e.get("event_type") != "component_event":
            continue
        key = e.get("key")
        if not isinstance(key, str) or not key:
            continue
        status = e.get("status")
        ts_us = _to_int_us(e.get("inserted_timestamp"))
        if ts_us is None:
            continue
        rec = by_key.setdefault(key, {"start_us": None, "end_us": None, "title": None, "component_type": None})
        if isinstance(e.get("title"), str) and e.get("title"):
            rec["title"] = e.get("title")
        if isinstance(e.get("component_type"), str) and e.get("component_type"):
            rec["component_type"] = e.get("component_type")
        if status == "in_progress":
            if rec["start_us"] is None or ts_us < rec["start_us"]:
                rec["start_us"] = ts_us
        elif status == "done":
            if rec["end_us"] is None or ts_us > rec["end_us"]:
                rec["end_us"] = ts_us

    rows: List[Tuple[str, str, str, int, int, float]] = []
    for key, rec in by_key.items():
        su = rec.get("start_us")
        eu = rec.get("end_us")
        if isinstance(su, int) and isinstance(eu, int) and eu >= su:
            title = rec.get("title") or ""
            ctype = rec.get("component_type") or ""
            duration_ms = (eu - su) / 1000.0
            rows.append((key, title, ctype, su, eu, duration_ms))
    rows.sort(key=lambda r: r[3])
    return rows


def _gap_ms(prev_end_us: Optional[int], cur_start_us: int) -> Optional[float]:
    if prev_end_us is None:
        return None
    return (cur_start_us - prev_end_us) / 1000.0


def build_component_timings(report_dir: Path, project_code: str = "TEST12", branch: str = "master") -> Path:
    """
    Строит CSV файлы:
    1. component_timings.csv - общий файл со всеми компонентами
    2. component_timings_{request_id}.csv - отдельный файл для каждого запроса
    3. component_timings_aggregated.csv - агрегированная статистика по компонентам
    """
    jobs_csv = report_dir / "jobs_from_responses.csv"
    out_csv = report_dir / "component_timings.csv"
    aggregated_csv = report_dir / "component_timings_aggregated.csv"

    jobs = load_jobs_from_responses_csv(jobs_csv)
    if not jobs:
        print(f"[COMPONENT_TIMINGS] В {jobs_csv} нет записей, отчёт не будет создан.")
        return out_csv

    # Стабильные totals для отчётов:
    # - attempted_requests: сколько попыток было сделано (строк в jobs_from_responses.csv)
    # - successful_requests: сколько успешных джоб (status=finished и есть job_uuid)
    attempted_requests = len(jobs)
    successful_request_ids: List[str] = []
    for j in jobs:
        rid = (j.get("request_id") or "").strip()
        status = (j.get("status") or "").strip().lower()
        job_uuid = (j.get("job_uuid") or "").strip()
        if rid and status == "finished" and job_uuid:
            successful_request_ids.append(rid)
    successful_requests = len(successful_request_ids)

    # Попробуем сначала использовать component_timings.csv, если Locust уже собрал его
    # напрямую при прогоне (через _write_component_rows). Если там есть строки данных,
    # не будем повторно опрашивать /api/events/{job_uuid}.
    use_existing_timings = False
    all_rows: List[Dict[str, Any]] = []
    by_request: Dict[str, List[Dict[str, Any]]] = {}
    first_seen_component_order: Dict[str, int] = {}
    first_seen_group_order: Dict[str, int] = {}
    _row_seq = 0

    if out_csv.exists():
        with out_csv.open("r", encoding="utf-8") as f_exist:
            reader_exist = list(csv.DictReader(f_exist))
        if reader_exist:
            use_existing_timings = True
            print(f"[COMPONENT_TIMINGS] Используем уже собранный Locust'ом component_timings.csv "
                  f"({len(reader_exist)} строк) из {out_csv}")

            for row in reader_exist:
                request_id = row.get("request_id")
                job_uuid = row.get("job_uuid")
                key = row.get("component_key")
                title = row.get("component_title") or ""
                ctype = row.get("component_type") or ""
                start_us = _to_int_us(row.get("start_us"))
                end_us = _to_int_us(row.get("end_us"))
                try:
                    duration_ms = float(row.get("duration_ms") or 0)
                except Exception:
                    duration_ms = 0.0
                gap_raw = row.get("gap_from_prev_ms")
                try:
                    gap_val = float(gap_raw) if gap_raw not in ("", None) else None
                except Exception:
                    gap_val = None

                title_meta = parse_component_title_hierarchy(title)
                _row_seq += 1
                row_data = {
                    "request_id": request_id,
                    "job_uuid": job_uuid,
                    "component_key": key,
                    "component_title": title,
                    "component_title_base": title_meta["title_base"],
                    "component_title_level": title_meta["title_level"],
                    "component_title_path": title_meta["title_path"],
                    "component_type": ctype,
                    "start_us": start_us,
                    "end_us": end_us,
                    "duration_ms": duration_ms,
                    "gap_from_prev_ms": gap_val,
                }
                all_rows.append(row_data)
                if request_id:
                    by_request.setdefault(request_id, []).append(row_data)

                # порядок компонентов: по первому появлению в выполнении
                if title and title not in first_seen_component_order:
                    first_seen_component_order[title] = _row_seq

                base_for_group = row_data.get("component_title_base") or title
                if base_for_group and base_for_group not in first_seen_group_order:
                    first_seen_group_order[base_for_group] = _row_seq

    if not use_existing_timings:
        api = ProjectProcessLogAPI(project_code=project_code, branch=branch)

        for job in jobs:
            request_id = job.get("request_id")
            job_uuid = job.get("job_uuid")
            if not job_uuid:
                continue
            try:
                payload = api.get_job_events(job_uuid)
            except Exception as e:
                print(f"[COMPONENT_TIMINGS] Ошибка при запросе events для job_uuid={job_uuid}: {e}")
                continue

            events = _extract_events(payload)
            rows = _compute_component_rows(events)

            request_rows = []
            prev_end: Optional[int] = None
            for key, title, ctype, start_us, end_us, duration_ms in rows:
                gap = _gap_ms(prev_end, start_us)
                title_meta = parse_component_title_hierarchy(title)
                _row_seq += 1
                row_data = {
                    "request_id": request_id,
                    "job_uuid": job_uuid,
                    "component_key": key,
                    "component_title": title,  # сохраняем как есть
                    "component_title_base": title_meta["title_base"],
                    "component_title_level": title_meta["title_level"],
                    "component_title_path": title_meta["title_path"],
                    "component_type": ctype,
                    "start_us": start_us,
                    "end_us": end_us,
                    "duration_ms": duration_ms,
                    "gap_from_prev_ms": gap,
                }
                all_rows.append(row_data)
                request_rows.append(row_data)
                prev_end = end_us

                # порядок компонентов: по первому появлению в выполнении
                if title and title not in first_seen_component_order:
                    first_seen_component_order[title] = _row_seq

                base_for_group = row_data.get("component_title_base") or title
                if base_for_group and base_for_group not in first_seen_group_order:
                    first_seen_group_order[base_for_group] = _row_seq
            
            if request_id:
                by_request[request_id] = request_rows

    # Записываем общий файл
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "request_id",
            "job_uuid",
            "component_key",
            "component_title",
            "component_title_base",
            "component_title_level",
            "component_title_path",
            "component_type",
            "start_us",
            "end_us",
            "duration_ms",
            "gap_from_prev_ms",
        ])
        for row in all_rows:
            w.writerow([
                row["request_id"],
                row["job_uuid"],
                row["component_key"],
                row["component_title"],
                row["component_title_base"],
                row["component_title_level"] if row["component_title_level"] is not None else "",
                row["component_title_path"],
                row["component_type"],
                row["start_us"],
                row["end_us"],
                f"{row['duration_ms']:.3f}",
                ("" if row['gap_from_prev_ms'] is None else f"{row['gap_from_prev_ms']:.3f}"),
            ])

    # Записываем отдельные файлы для каждого запроса
    for request_id, rows in by_request.items():
        request_csv = report_dir / f"component_timings_{request_id[:8]}.csv"
        with request_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "request_id",
                "job_uuid",
                "component_key",
                "component_title",
                "component_title_base",
                "component_title_level",
                "component_title_path",
                "component_type",
                "start_us",
                "end_us",
                "duration_ms",
                "gap_from_prev_ms",
            ])
            for row in rows:
                w.writerow([
                    row["request_id"],
                    row["job_uuid"],
                    row["component_key"],
                    row["component_title"],
                    row["component_title_base"],
                    row["component_title_level"] if row["component_title_level"] is not None else "",
                    row["component_title_path"],
                    row["component_type"],
                    row["start_us"],
                    row["end_us"],
                    f"{row['duration_ms']:.3f}",
                    ("" if row['gap_from_prev_ms'] is None else f"{row['gap_from_prev_ms']:.3f}"),
                ])

    # Строим агрегированную статистику по компонентам (и сохраняем все значения по прогонам)
    from collections import defaultdict
    import statistics
    
    # request_id в порядке прогонов (attempts), для графиков/порядка
    all_request_ids = [job.get("request_id") for job in jobs if job.get("request_id")]
    
    by_component: Dict[str, List[float]] = defaultdict(list)
    by_component_runs: Dict[str, Dict[str, float]] = defaultdict(dict)  # {request_id: duration_ms}
    by_component_gaps: Dict[str, List[float]] = defaultdict(list)  # задержки между компонентами
    component_metadata: Dict[str, Dict[str, Any]] = {}
    
    for row in all_rows:
        title = row["component_title"]  # агрегат по конкретному имени (как раньше)
        if not title:
            continue
        duration = row["duration_ms"]
        gap = row.get("gap_from_prev_ms")
        request_id = row.get("request_id")
        
        by_component[title].append(duration)
        if request_id:
            by_component_runs[title][request_id] = duration
        
        # Собираем задержки (только валидные, не None и не пустые)
        if gap is not None and gap != "":
            try:
                gap_val = float(gap)
                if gap_val >= 0:  # Отрицательные задержки — это параллельное выполнение, не учитываем
                    by_component_gaps[title].append(gap_val)
            except (ValueError, TypeError):
                pass
        
        if title not in component_metadata:
            component_metadata[title] = {
                "component_type": row["component_type"],
                "component_key": row["component_key"],
                "component_title_base": row["component_title_base"],
                "component_title_level": row["component_title_level"],
                "component_title_path": row["component_title_path"],
            }
    
    # Записываем агрегированный файл
    with aggregated_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "component_title",
            "component_title_base",
            "component_title_level",
            "component_title_path",
            "component_type",
            "component_key",
            "count",
            "total_requests",
            "attempted_requests",
            "avg_ms",
            "min_ms",
            "max_ms",
            "median_ms",
            "stddev_ms",
            "avg_gap_ms",
            "min_gap_ms",
            "max_gap_ms",
            "median_gap_ms",
            "runs_request_id",
            "runs_ms",
        ])
        
        # Важно: порядок — как в выполнении (по первому появлению)
        titles_in_order = sorted(by_component.keys(), key=lambda t: first_seen_component_order.get(t, 10**18))
        for title in titles_in_order:
            durations = by_component[title]
            if durations:
                metadata = component_metadata.get(title, {})
                runs_dict = by_component_runs.get(title, {})
                
                # Сохраняем в порядке прогонов: все request_id, но только те, где компонент выполнился
                runs_request_ids_list = []
                runs_ms_list = []
                
                for req_id in all_request_ids:
                    if req_id in runs_dict:
                        runs_request_ids_list.append(req_id[:8])
                        runs_ms_list.append(f"{runs_dict[req_id]:.3f}")
                    # Если компонент не выполнился в этом запросе, не добавляем его в список
                    # (это нормально для условной логики)
                
                runs_request_ids = ",".join(runs_request_ids_list)
                runs_ms = ",".join(runs_ms_list)
                
                # Статистика по задержкам
                gaps = by_component_gaps.get(title, [])
                if gaps:
                    avg_gap = f"{statistics.mean(gaps):.3f}"
                    min_gap = f"{min(gaps):.3f}"
                    max_gap = f"{max(gaps):.3f}"
                    median_gap = f"{statistics.median(gaps):.3f}"
                else:
                    avg_gap = min_gap = max_gap = median_gap = ""
                
                w.writerow([
                    title,
                    metadata.get("component_title_base", ""),
                    metadata.get("component_title_level", "") if metadata.get("component_title_level", None) is not None else "",
                    metadata.get("component_title_path", ""),
                    metadata.get("component_type", ""),
                    metadata.get("component_key", ""),
                    len(durations),  # Реальное количество выполнений
                    successful_requests,  # Успешные из attempts (то, для чего ожидаем component events)
                    attempted_requests,  # Всего attempts (то, что ты задал в --num-requests)
                    f"{statistics.mean(durations):.3f}",
                    f"{min(durations):.3f}",
                    f"{max(durations):.3f}",
                    f"{statistics.median(durations):.3f}",
                    f"{statistics.stdev(durations):.3f}" if len(durations) > 1 else "0.000",
                    avg_gap,
                    min_gap,
                    max_gap,
                    median_gap,
                    runs_request_ids,
                    runs_ms,
                ])

    # Дополнительно: агрегируем "схлопнуто" по базовому имени (без _testN), чтобы test1/test2/test3 было читаемо
    grouped_csv = report_dir / "component_timings_grouped.csv"
    by_group: Dict[str, List[float]] = defaultdict(list)
    by_group_runs: Dict[str, Dict[str, float]] = defaultdict(dict)
    by_group_gaps: Dict[str, List[float]] = defaultdict(list)  # задержки для групп
    group_meta: Dict[str, Dict[str, Any]] = {}

    for row in all_rows:
        base = row.get("component_title_base") or row.get("component_title") or ""
        if not base:
            continue
        duration = row["duration_ms"]
        gap = row.get("gap_from_prev_ms")
        rid = row.get("request_id")
        by_group[base].append(duration)
        if rid:
            # если в одном запросе base встретился несколько раз (редко) — суммируем
            by_group_runs[base][rid] = by_group_runs[base].get(rid, 0.0) + float(duration)
        
        # Собираем задержки для группы
        if gap is not None and gap != "":
            try:
                gap_val = float(gap)
                if gap_val >= 0:
                    by_group_gaps[base].append(gap_val)
            except (ValueError, TypeError):
                pass
        
        if base not in group_meta:
            group_meta[base] = {"example_title": row.get("component_title", ""), "component_type": row.get("component_type", "")}

    with grouped_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "group_title_base",
            "example_title",
            "component_type",
            "count",
            "total_requests",
            "attempted_requests",
            "avg_ms",
            "min_ms",
            "max_ms",
            "median_ms",
            "stddev_ms",
            "avg_gap_ms",
            "min_gap_ms",
            "max_gap_ms",
            "median_gap_ms",
            "runs_request_id",
            "runs_ms",
        ])
        # Порядок групп — как в выполнении (по первому появлению базового имени)
        groups_in_order = sorted(by_group.keys(), key=lambda t: first_seen_group_order.get(t, 10**18))
        for base in groups_in_order:
            durations = by_group[base]
            if not durations:
                continue
            runs_dict = by_group_runs.get(base, {})
            runs_request_ids_list = []
            runs_ms_list = []
            for req_id in all_request_ids:
                if req_id in runs_dict:
                    runs_request_ids_list.append(req_id[:8])
                    runs_ms_list.append(f"{runs_dict[req_id]:.3f}")
            
            # Статистика по задержкам для группы
            gaps = by_group_gaps.get(base, [])
            if gaps:
                avg_gap = f"{statistics.mean(gaps):.3f}"
                min_gap = f"{min(gaps):.3f}"
                max_gap = f"{max(gaps):.3f}"
                median_gap = f"{statistics.median(gaps):.3f}"
            else:
                avg_gap = min_gap = max_gap = median_gap = ""
            
            w.writerow([
                base,
                group_meta.get(base, {}).get("example_title", ""),
                group_meta.get(base, {}).get("component_type", ""),
                len(durations),
                successful_requests,
                attempted_requests,
                f"{statistics.mean(durations):.3f}",
                f"{min(durations):.3f}",
                f"{max(durations):.3f}",
                f"{statistics.median(durations):.3f}",
                f"{statistics.stdev(durations):.3f}" if len(durations) > 1 else "0.000",
                avg_gap,
                min_gap,
                max_gap,
                median_gap,
                ",".join(runs_request_ids_list),
                ",".join(runs_ms_list),
            ])

    print(f"[COMPONENT_TIMINGS] Общий отчёт сохранён в {out_csv}")
    print(f"[COMPONENT_TIMINGS] Создано {len(by_request)} отдельных файлов по запросам")
    print(f"[COMPONENT_TIMINGS] Агрегированный отчёт сохранён в {aggregated_csv}")
    print(f"[COMPONENT_TIMINGS] Групповой отчёт сохранён в {grouped_csv}")
    return out_csv


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(description="Строит отчёт component_timings.csv по компонентам процесса")
    p.add_argument(
        "--report-dir",
        type=str,
        required=True,
        help="Путь к директории отчёта Locust (содержит jobs_from_responses.csv)",
    )
    p.add_argument(
        "--project-code",
        type=str,
        default="TEST12",
        help="Код проекта (по умолчанию TEST12)",
    )
    p.add_argument(
        "--branch",
        type=str,
        default="master",
        help="Ветка проекта (по умолчанию master)",
    )
    args = p.parse_args(argv)

    report_dir = Path(args.report_dir).resolve()
    build_component_timings(report_dir, project_code=args.project_code, branch=args.branch)


if __name__ == "__main__":
    main()

