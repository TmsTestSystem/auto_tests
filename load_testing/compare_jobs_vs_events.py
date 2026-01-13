import csv
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import datetime as dt
import html
import csv as _csv
import argparse


# Определяем базовую директорию (может быть переопределена для использования в load/)
base_dir_env = os.getenv('BASE_DIR')
if base_dir_env:
    BASE_ROOT = Path(base_dir_env)
else:
    BASE_ROOT = Path(__file__).parent


def load_started_events(events_csv_path: Path) -> Dict[str, dt.datetime]:
    """Загружает события STARTED из requests_events.csv и создаёт маппинг request_id -> datetime (naive UTC).
    Формат времени в CSV: date=DD.MM.YYYY, time=HH:MM:SS.fffff (опционально с суффиксом 'Z').
    """
    request_id_to_started: Dict[str, dt.datetime] = {}
    with events_csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row or len(row) < 6:
                continue
            event_type, event_date, event_time = row[0], row[1], row[2]
            if event_type != "STARTED":
                continue
            rid = row[5]
            time_no_z = event_time.rstrip("Z")
            # Naive datetime (обрабатываем как UTC для сравнения)
            started_dt = dt.datetime.strptime(
                f"{event_date} {time_no_z}", "%d.%m.%Y %H:%M:%S.%f"
            )
            request_id_to_started[rid] = started_dt
    return request_id_to_started


def load_jobs(jobs_json_path: Path) -> List[Dict[str, Any]]:
    """Загружает список jobs из jobs.json, где API может вернуть массив или объект с items."""
    text = jobs_json_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "items" in data:
            return list(data["items"])  # type: ignore[index]
        if isinstance(data, list):
            return list(data)
    except Exception:
        pass

    # Резервный вариант: извлекаем первый JSON массив из текста
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    return []


def load_jobs_from_responses_csv(path: Path) -> List[Dict[str, Any]]:
    """Загружает jobs из CSV, захваченного Locust (jobs_from_responses.csv)."""
    jobs: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            # Нормализуем к схеме, похожей на API
            jobs.append({
                "request_id": row.get("request_id"),
                "object_id": row.get("object_id"),
                "status": row.get("status"),
                "path": row.get("path"),
                "started_at": row.get("started_at"),
                "finished_at": row.get("finished_at"),
                "job_duration": (int(row.get("job_duration")) if (row.get("job_duration") and row.get("job_duration").isdigit()) else row.get("job_duration")),
                "job_uuid": row.get("job_uuid"),
            })
    return jobs


def compare_times(
    started_map: Dict[str, dt.datetime],
    jobs: List[Dict[str, Any]],
    req_metrics: Dict[str, Dict[str, int]],
    objid_to_endms: Dict[str, int] = None,
) -> List[Dict[str, Any]]:
    if objid_to_endms is None:
        objid_to_endms = {}
    """Для каждого совпадающего request_id вычисляет:

    Низкоуровневые дельты (исторические поля):
    - delta_started_at_vs_object_id_ms
    - delta_finished_at_vs_response_end_ms
    - delta_job_duration_vs_object_to_response_end_ms (job_duration - (response_end - object_id))

    Бизнес-ориентированные таймстемпы и метрики под ТЗ:
    - RequestSent_DT        : момент отправки запроса (по STARTED event / started_map)
    - EvalStart_DT          : момент начала выполнения бизнес-логики (started_at из job)
    - EvalEnd_DT            : момент окончания выполнения (finished_at из job)
    - ResponseReceived_DT   : момент получения ответа клиентом (response_end по Locust)
    - Delay_ReqEval_ms      : EvalStart_DT - RequestSent_DT
    - Duration_Eval_ms      : EvalEnd_DT   - EvalStart_DT
    - Delay_Eval_Resp_ms    : ResponseReceived_DT - EvalEnd_DT

    Возвращает список словарей для удобного вывода/анализа.
    """
    results: List[Dict[str, Any]] = []
    skipped_no_rid = 0
    skipped_no_obj = 0
    skipped_no_sa = 0
    skipped_no_fa = 0
    skipped_not_in_started_map = 0
    for job in jobs:
        rid = job.get("request_id")
        obj = job.get("object_id")  # "DD.MM.YYYY HH:MM:SS.fffff"
        sa = job.get("started_at")  # ISO UTC строка
        fa = job.get("finished_at")  # ISO UTC строка
        job_duration = job.get("job_duration")  # уже в миллисекундах согласно API
        if not rid:
            skipped_no_rid += 1
            continue
        if not obj:
            skipped_no_obj += 1
            continue
        if not sa:
            skipped_no_sa += 1
            continue
        if not fa:
            skipped_no_fa += 1
            continue
        if rid not in started_map:
            skipped_not_in_started_map += 1
            continue

        # object_id может быть с суффиксом 'Z' (UTC). Уберём 'Z' при парсинге.
        try:
            obj_dt = dt.datetime.strptime(obj.rstrip('Z'), "%d.%m.%Y %H:%M:%S.%f")
        except Exception:
            continue

        try:
            sa_dt = dt.datetime.fromisoformat(sa)
        except Exception:
            continue

        # Нормализуем started_at/finished_at к naive UTC для вычисления разницы
        if sa_dt.tzinfo is not None:
            sa_dt = sa_dt.astimezone(dt.timezone.utc).replace(tzinfo=None)
        try:
            fa_dt = dt.datetime.fromisoformat(fa)
            if fa_dt.tzinfo is not None:
                fa_dt = fa_dt.astimezone(dt.timezone.utc).replace(tzinfo=None)
        except Exception:
            continue

        ev_dt = started_map[rid]
        d_started_ms = int((sa_dt - ev_dt).total_seconds() * 1000)
        d_object_ms = int((obj_dt - ev_dt).total_seconds() * 1000)
        db_duration_ms = int((fa_dt - sa_dt).total_seconds() * 1000)

        # Locust metrics - сначала по request_id, потом fallback по object_id
        rm = req_metrics.get(rid)
        response_time_ms = rm.get("response_time_ms", -1) if rm else -1
        end_ms = rm.get("timestamp_end_ms") if rm else None
        
        # Fallback: если не нашли по request_id, пробуем найти по object_id
        # object_id может быть в формате "DD.MM.YYYY HH:MM:SS.fffff" или "DD.MM.YYYY HH:MM:SS.fffffZ"
        if end_ms is None and objid_to_endms:
            # Пробуем точное совпадение
            if obj in objid_to_endms:
                end_ms = objid_to_endms[obj]
            # Пробуем без 'Z' в конце
            elif obj.rstrip('Z') in objid_to_endms:
                end_ms = objid_to_endms[obj.rstrip('Z')]
            # Пробуем с 'Z' в конце
            elif obj + 'Z' in objid_to_endms:
                end_ms = objid_to_endms[obj + 'Z']

        # Вычисляем время response_end, если доступно
        response_end_dt = None
        if end_ms is not None:
            # end_ms это epoch миллисекунды UTC
            response_end_dt = dt.datetime.utcfromtimestamp(end_ms / 1000.0)

        # Вычисленные сравнения согласно требованиям
        delta_started_at_vs_object_id_ms = int((sa_dt - obj_dt).total_seconds() * 1000)
        delta_finished_at_vs_response_end_ms = (
            int((fa_dt - response_end_dt).total_seconds() * 1000)
            if response_end_dt is not None
            else None
        )
        delta_object_id_to_response_end_ms = (
            int((response_end_dt - obj_dt).total_seconds() * 1000)
            if response_end_dt is not None
            else None
        )
        delta_job_duration_vs_object_to_response_end_ms = (
            (int(job_duration) - delta_object_id_to_response_end_ms)
            if (job_duration is not None and delta_object_id_to_response_end_ms is not None)
            else None
        )

        # Бизнесовые метрики под ТЗ
        # RequestSent_DT: когда система приняла запрос (STARTED event)
        request_sent_dt = ev_dt  # naive UTC (без таймзоны)
        # EvalStart_DT / EvalEnd_DT: как есть в API (строки, могут быть с таймзоной)
        eval_start_dt_raw = sa
        eval_end_dt_raw = fa
        # ResponseReceived_DT: момент окончания HTTP‑запроса с точки зрения клиента
        response_received_dt = response_end_dt

        delay_req_eval_ms = int((sa_dt - ev_dt).total_seconds() * 1000)
        duration_eval_ms = db_duration_ms
        delay_eval_resp_ms: Any
        if response_end_dt is not None:
            delay_eval_resp_ms = int((response_end_dt - fa_dt).total_seconds() * 1000)
        else:
            delay_eval_resp_ms = None

        results.append(
            {
                "request_id": rid,
                # Бизнесовые таймстемпы/метрики под ТЗ
                "RequestSent_DT": request_sent_dt.isoformat(sep=" "),
                "EvalStart_DT": eval_start_dt_raw,
                "EvalEnd_DT": eval_end_dt_raw,
                "ResponseReceived_DT": (
                    response_received_dt.isoformat(sep=" ")
                    if response_received_dt is not None
                    else None
                ),
                "Delay_ReqEval_ms": delay_req_eval_ms,
                "Duration_Eval_ms": duration_eval_ms,
                "Delay_Eval_Resp_ms": delay_eval_resp_ms,
            }
        )

    # Сортируем по Delay_ReqEval_ms (время от отправки до начала выполнения)
    results.sort(key=lambda x: abs(x.get("Delay_ReqEval_ms", 0)) if x.get("Delay_ReqEval_ms") is not None else 0)
    if skipped_no_rid > 0 or skipped_no_obj > 0 or skipped_no_sa > 0 or skipped_no_fa > 0 or skipped_not_in_started_map > 0:
        print(f"DEBUG: Skipped jobs - no_rid={skipped_no_rid}, no_obj={skipped_no_obj}, no_sa={skipped_no_sa}, no_fa={skipped_no_fa}, not_in_started_map={skipped_not_in_started_map}")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Генерирует отчёт сравнения с опциональной фильтрацией/выборкой")
    parser.add_argument("--delta-range-ms", nargs=2, type=int, metavar=("MIN","MAX"), help="Filter by Delay_ReqEval_ms in [MIN, MAX]")
    parser.add_argument("--abs-delta-top", type=int, default=None, help="Keep top-N by |delta_started_at_vs_object_id_ms|")
    parser.add_argument("--bucket-ms", type=int, default=None, help="Bucket size in ms for delta_started_at_vs_object_id_ms")
    parser.add_argument("--samples-per-bucket", type=int, default=3, help="Samples per bucket to keep (with --bucket-ms)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows in table/filtered CSV")
    parser.add_argument("--columns", type=str, default=None, help="Comma-separated list of columns to include in table/CSV")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = BASE_ROOT
    # Если задан REPORT_DIR, используем ТОЛЬКО файлы из него (без fallback на старые данные)
    env_dir = os.getenv('REPORT_DIR')
    if env_dir:
        report_dir_path = Path(env_dir)
        # Используем ТОЛЬКО файлы из REPORT_DIR, чтобы не смешивать с данными из прошлых запусков
        events_csv = report_dir_path / "requests_events.csv"
        requests_csv = report_dir_path / "requests.csv"
        print(f"[REPORT] Используем только данные из REPORT_DIR: {report_dir_path}")
        if not events_csv.exists():
            print(f"[REPORT_WARN] requests_events.csv не найден в REPORT_DIR: {events_csv}")
        if not requests_csv.exists():
            print(f"[REPORT_WARN] requests.csv не найден в REPORT_DIR: {requests_csv}")
    else:
        # Предпочитаем явный файл событий; поддерживаем устаревшие/альтернативные названия
        events_csv_candidates = [
            root / "locust_logs" / "requests_events.csv",
            root / "locust_logs" / "requests_data_time.csv",
        ]
        events_csv = next((p for p in events_csv_candidates if p.exists()), events_csv_candidates[0])
        # CSV запросов: предпочитаем последний вариант с временной меткой requests_YYYYMMDD_HHMMSS.csv, иначе requests.csv
        # НЕ включаем requests_events.csv и requests_report.csv - это другие файлы!
        requests_dir = root / "locust_logs"
        if requests_dir.exists():
            # Сначала пробуем точное имя requests.csv
            exact_file = requests_dir / "requests.csv"
            if exact_file.exists():
                requests_csv = exact_file
            else:
                # Ищем файлы с паттерном requests_YYYYMMDD_HHMMSS.csv (без _report и _events)
                all_csvs = list(requests_dir.glob("requests_*.csv"))
                # Исключаем requests_events.csv и requests_report.csv
                ts_req_candidates = sorted(
                    [p for p in all_csvs if "events" not in p.name.lower() and "report" not in p.name.lower()],
                    key=lambda x: x.stat().st_mtime
                )
                requests_csv = ts_req_candidates[-1] if ts_req_candidates else (requests_dir / "requests.csv")
        else:
            requests_csv = requests_dir / "requests.csv"
    jobs_json = root / "jobs.json"
    # Предпочитаем CSV ответов для каждого запуска - если задан REPORT_DIR, используем ТОЛЬКО его
    responses_csv = None
    env_dir = os.getenv('REPORT_DIR')
    if env_dir:
        report_dir_path = Path(env_dir)
        p = report_dir_path / 'jobs_from_responses.csv'
        if p.exists():
            responses_csv = p
            print(f"[REPORT] Найден jobs_from_responses.csv в REPORT_DIR: {responses_csv}")
        else:
            print(f"[REPORT_WARN] jobs_from_responses.csv не найден в REPORT_DIR: {p}")
    else:
        # Резервный вариант на старые данные только если REPORT_DIR не задан
        # Пробуем родительский locust_logs проекта (при запуске под load/)
        parent_logs = root.parent / 'locust_logs'
        if parent_logs.exists():
            candidates = sorted(parent_logs.glob('jobs_from_responses_*.csv'), key=lambda x: x.stat().st_mtime)
            if candidates:
                responses_csv = candidates[-1]
                print(f"Найден последний CSV jobs_from_responses с временной меткой в родительском locust_logs: {responses_csv}")
            else:
                p = parent_logs / 'jobs_from_responses.csv'
                if p.exists():
                    responses_csv = p
                    print(f"Найден jobs_from_responses.csv в родительском locust_logs: {responses_csv}")
        if responses_csv is None:
            # Пробуем последний файл с временной меткой в BASE_ROOT/locust_logs
            if (root / 'locust_logs').exists():
                candidates = sorted((root / 'locust_logs').glob('jobs_from_responses_*.csv'), key=lambda x: x.stat().st_mtime)
                if candidates:
                    responses_csv = candidates[-1]
                    print(f"Найден последний CSV jobs_from_responses с временной меткой в locust_logs: {responses_csv}")
                else:
                    p = root / 'locust_logs' / 'jobs_from_responses.csv'
                    if p.exists():
                        responses_csv = p
                        print(f"Найден jobs_from_responses.csv в locust_logs: {responses_csv}")

    if responses_csv:
        print(f"Используем CSV ответов: {responses_csv}")

    if not events_csv.exists():
        print(f"CSV событий не найден: {events_csv}")
    if (responses_csv is None or not responses_csv.exists()) and not jobs_json.exists():
        print(f"Источники jobs не найдены. Отсутствуют: {jobs_json} и {responses_csv}")
        return 1

    # Загружаем метрики ответов из requests.csv по request_id и по вычисленному object_id
    req_metrics: Dict[str, Dict[str, int]] = {}
    objid_to_endms: Dict[str, int] = {}
    # Если есть ответы, собираем их request_ids для ограничения соединения
    response_request_ids = set()
    if responses_csv and responses_csv.exists():
        try:
            with responses_csv.open('r', encoding='utf-8') as rf:
                rr = _csv.DictReader(rf)
                for row in rr:
                    rid = row.get('request_id')
                    if rid:
                        response_request_ids.add(rid)
        except Exception:
            pass
    if requests_csv.exists():
        with requests_csv.open("r", encoding="utf-8") as rf:
            reader = csv.reader(rf)
            header = next(reader, None) or []
            # Find indices - проверяем разные варианты названий колонок
            try:
                idx_request_id = header.index("request_id")
            except ValueError:
                try:
                    idx_request_id = header.index("request_id")
                except ValueError:
                    idx_request_id = -1
            try:
                idx_response_time = header.index("response_time_ms")
            except ValueError:
                # Пробуем альтернативные названия
                try:
                    idx_response_time = header.index("duration_ms")
                except ValueError:
                    idx_response_time = -1
            try:
                idx_start_ms = header.index("timestamp_start_ms")
            except ValueError:
                # В locustfile.py записывается start_ms (первая колонка)
                idx_start_ms = 0 if len(header) > 0 else -1
            try:
                idx_end_ms = header.index("timestamp_end_ms")
            except ValueError:
                # В locustfile.py записывается end_ms (третья колонка)
                idx_end_ms = 2 if len(header) > 2 else -1
            if idx_request_id >= 0 and idx_response_time >= 0 and idx_end_ms >= 0:
                for row in reader:
                    if not row or len(row) <= max(idx_request_id, idx_response_time, idx_end_ms):
                        continue
                    rid = row[idx_request_id]
                    # Загружаем все метрики из requests.csv, не фильтруя по response_request_ids
                    # Это позволит заполнить ResponseReceived_DT даже если request_id не совпадает точно
                    # (ранее был фильтр: if response_request_ids and rid not in response_request_ids: continue)
                    try:
                        resp_ms = int(float(row[idx_response_time]))
                        end_ms = int(float(row[idx_end_ms]))
                        start_ms = int(float(row[idx_start_ms])) if idx_start_ms >= 0 else None
                    except Exception:
                        continue
                    req_metrics[rid] = {
                        "response_time_ms": resp_ms,
                        "timestamp_end_ms": end_ms,
                        **({"timestamp_start_ms": start_ms} if start_ms is not None else {}),
                    }
                    # Вычисляем строку object_id из start_ms для резервного соединения
                    # Формат должен совпадать с тем, что создаётся в locustfile.py:
                    # object_id = f"{started_date} {started_time}" где started_time = f"{now.strftime('%H:%M:%S')}.{now.strftime('%f')[:5]}Z"
                    if start_ms is not None:
                        try:
                            start_dt_utc = dt.datetime.utcfromtimestamp(start_ms / 1000.0)
                            obj_date = start_dt_utc.strftime("%d.%m.%Y")
                            # Формат с 'Z' в конце (как в locustfile.py)
                            obj_time = f"{start_dt_utc.strftime('%H:%M:%S')}.{start_dt_utc.strftime('%f')[:5]}Z"
                            object_id_str = f"{obj_date} {obj_time}"
                            objid_to_endms[object_id_str] = end_ms
                            # Также добавляем вариант без 'Z' для совместимости (если API возвращает без 'Z')
                            objid_to_endms[object_id_str.rstrip('Z')] = end_ms
                        except Exception:
                            pass

    # Строим started_map:
    # - Предпочитаем события STARTED из requests_events.csv, если присутствуют
    # - Если отсутствуют, вычисляем из requests.csv timestamp_start_ms (UTC epoch миллисекунды)
    if events_csv.exists():
        started_map = load_started_events(events_csv)
    else:
        started_map = {}
        # Основной вариант: вычисляем из req_metrics (уже распарсено из requests.csv)
        if req_metrics:
            for rid, m in req_metrics.items():
                start_ms = m.get("timestamp_start_ms")
                if start_ms is None:
                    continue
                try:
                    started_map[rid] = dt.datetime.utcfromtimestamp(start_ms / 1000.0)
                except Exception:
                    continue
        # Резервный вариант: читаем requests.csv напрямую, если всё ещё пусто
        if not started_map and requests_csv.exists():
            try:
                with requests_csv.open("r", encoding="utf-8") as rf2:
                    rdr2 = csv.reader(rf2)
                    hdr2 = next(rdr2, None) or []
                    try:
                        rid_idx = hdr2.index("request_id")
                        start_idx = hdr2.index("timestamp_start_ms")
                    except ValueError:
                        rid_idx = start_idx = -1
                    if rid_idx >= 0 and start_idx >= 0:
                        for row in rdr2:
                            if not row or len(row) <= max(rid_idx, start_idx):
                                continue
                            rid2 = row[rid_idx]
                            try:
                                start_ms2 = int(float(row[start_idx]))
                                started_map[rid2] = dt.datetime.utcfromtimestamp(start_ms2 / 1000.0)
                            except Exception:
                                continue
            except Exception:
                pass
        print(f"Вычислена карта STARTED из requests.csv: {len(started_map)} записей")
    # Предпочитаем CSV, собранный из ответов; резервный вариант - jobs.json
    if responses_csv:
        jobs = load_jobs_from_responses_csv(responses_csv)
        print(f"Loaded jobs from responses CSV: {len(jobs)} records")
        if len(jobs) > 0:
            print(f"Sample job keys: {list(jobs[0].keys()) if jobs else 'N/A'}")
            print(f"Sample job request_id: {jobs[0].get('request_id') if jobs else 'N/A'}")
            print(f"Sample job object_id: {jobs[0].get('object_id') if jobs else 'N/A'}")
    else:
        jobs = load_jobs(jobs_json)
        print(f"Loaded jobs from jobs.json: {len(jobs)} records")
    
    print(f"started_map size: {len(started_map)}")
    if started_map:
        sample_rids = list(started_map.keys())[:3]
        print(f"Sample started_map request_ids: {sample_rids}")
    
    print(f"req_metrics size: {len(req_metrics)}")
    if req_metrics:
        sample_req_rids = list(req_metrics.keys())[:3]
        print(f"Sample req_metrics request_ids: {sample_req_rids}")
    
    print(f"objid_to_endms size: {len(objid_to_endms)}")
    if objid_to_endms:
        sample_objids = list(objid_to_endms.keys())[:3]
        print(f"Sample objid_to_endms object_ids: {sample_objids}")
    
    # Загружены req_metrics и objid_to_endms для сопоставления данных
    results = compare_times(started_map, jobs, req_metrics, objid_to_endms)

    # Диагностика: сколько строк имеют response_end
    has_resp_end = sum(1 for r in results if r.get("ResponseReceived_DT") is not None)
    print(f"matched={len(results)} | with_response_end={has_resp_end}")
    for r in results[:20]:
        parts = [
            f"request_id={r['request_id']}",
            f"Delay_ReqEval_ms={r.get('Delay_ReqEval_ms')}",
            f"Duration_Eval_ms={r.get('Duration_Eval_ms')}",
            f"Delay_Eval_Resp_ms={r.get('Delay_Eval_Resp_ms')}",
            f"RequestSent_DT={r.get('RequestSent_DT')}",
            f"EvalStart_DT={r.get('EvalStart_DT')}",
            f"EvalEnd_DT={r.get('EvalEnd_DT')}",
            f"ResponseReceived_DT={r.get('ResponseReceived_DT')}",
        ]
        print(" | ".join(parts))

    # Оставляем только строки, где присутствуют response_end и дельты на основе job_duration
    valid_results = [
        r for r in results
        if r.get("ResponseReceived_DT") is not None
        and r.get("Delay_ReqEval_ms") is not None
        and r.get("Duration_Eval_ms") is not None
        and r.get("Delay_Eval_Resp_ms") is not None
    ]
    used_for_graphs = valid_results if valid_results else results

    # Применяем опциональную фильтрацию/выборку
    filtered: List[Dict[str, Any]] = list(used_for_graphs)
    # Фильтр по диапазону Delay_ReqEval_ms
    if args.delta_range_ms is not None:
        min_d, max_d = args.delta_range_ms
        filtered = [r for r in filtered if r.get("Delay_ReqEval_ms") is not None and min_d <= r["Delay_ReqEval_ms"] <= max_d]
    # Топ-N по абсолютной дельте
    if args.abs_delta_top is not None and args.abs_delta_top > 0:
        filtered = sorted(filtered, key=lambda r: abs(r.get("Delay_ReqEval_ms") or 0), reverse=True)[: args.abs_delta_top]
    # Группировка по дельте и выборка
    if args.bucket_ms is not None and args.bucket_ms > 0:
        from collections import defaultdict
        buckets: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for r in filtered:
            d = r.get("Delay_ReqEval_ms")
            if d is None:
                continue
            b = (d // args.bucket_ms) * args.bucket_ms
            if len(buckets[b]) < max(1, args.samples_per_bucket):
                buckets[b].append(r)
        # Разворачиваем в порядке групп
        filtered = []
        for b in sorted(buckets.keys()):
            filtered.extend(buckets[b])
    # Ограничиваем количество строк
    if args.limit is not None and args.limit > 0:
        filtered = filtered[: args.limit]

    # Выходная директория помечена датой-временем или предоставлена через env
    env_dir = os.getenv('REPORT_DIR')
    if env_dir:
        out_dir = Path(env_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        timestamp_str = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        out_dir = BASE_ROOT / 'reports' / timestamp_str
        out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Report directory: {out_dir}")

    # Строим HTML отчёт (таблица + графики по времени)
    report_path = out_dir / 'comparison_report.html'

    # Графики строим по всем данным (для полной картины)
    filtered_for_plot = filtered
    
    # Для таблицы в HTML: если запросов более 500 - каждую 10-ю, иначе каждую 2-ю
    # Полные данные всегда доступны в CSV
    if len(filtered) > 500:
        STEP_TABLE = 10
    else:
        STEP_TABLE = 2
    filtered_for_table = [filtered[i] for i in range(0, len(filtered), STEP_TABLE)]

    # Ось X — время по ResponseReceived_DT (если нет, то EvalEnd/EvalStart/RequestSent)
    labels_time = [
        (
            r.get("ResponseReceived_DT")
            or r.get("EvalEnd_DT")
            or r.get("EvalStart_DT")
            or r.get("RequestSent_DT")
            or ""
        )
        for r in filtered_for_plot
    ]

    # Метрики по ТЗ для графика - заменяем None на null для JavaScript
    series_delay_reqeval = [r.get("Delay_ReqEval_ms") if r.get("Delay_ReqEval_ms") is not None else None for r in filtered_for_plot]
    series_duration_eval = [r.get("Duration_Eval_ms") if r.get("Duration_Eval_ms") is not None else None for r in filtered_for_plot]
    series_delay_eval_resp = [r.get("Delay_Eval_Resp_ms") if r.get("Delay_Eval_Resp_ms") is not None else None for r in filtered_for_plot]

    # Преобразуем в JSON для безопасной вставки в JavaScript
    labels_js = json.dumps(labels_time, ensure_ascii=False)
    s_delay_reqeval_js = json.dumps(series_delay_reqeval, ensure_ascii=False)
    s_duration_eval_js = json.dumps(series_duration_eval, ensure_ascii=False)
    s_delay_eval_resp_js = json.dumps(series_delay_eval_resp, ensure_ascii=False)
    
    # Отладочная информация
    if not filtered_for_plot:
        print(f"[WARNING] Нет данных для графиков: filtered_for_plot пуст")
    else:
        print(f"[DEBUG] Графики: {len(filtered_for_plot)} точек, labels={len(labels_time)}, delay_reqeval={len(series_delay_reqeval)}")

    # Выбираем колонки - только метрики по ТЗ
    default_cols = [
        'request_id',
        'RequestSent_DT',
        'EvalStart_DT',
        'EvalEnd_DT',
        'ResponseReceived_DT',
        'Delay_ReqEval_ms',
        'Duration_Eval_ms',
        'Delay_Eval_Resp_ms',
    ]
    table_cols = [c.strip() for c in args.columns.split(',')] if args.columns else default_cols
    
    # Словарь с русскими описаниями колонок
    column_descriptions = {
        'request_id': 'ID запроса (UUID)',
        'RequestSent_DT': 'Момент отправки запроса (из STARTED event / requests.csv)',
        'EvalStart_DT': 'Момент начала выполнения бизнес-логики (started_at из ответа API /bps/call)',
        'EvalEnd_DT': 'Момент окончания выполнения (finished_at из ответа API /bps/call)',
        'ResponseReceived_DT': 'Момент получения ответа клиентом (timestamp_end_ms из requests.csv)',
        'Delay_ReqEval_ms': 'Задержка: время от отправки запроса до начала выполнения (EvalStart_DT - RequestSent_DT)',
        'Duration_Eval_ms': 'Длительность выполнения бизнес-логики (EvalEnd_DT - EvalStart_DT)',
        'Delay_Eval_Resp_ms': 'Задержка: время от окончания выполнения до получения ответа (ResponseReceived_DT - EvalEnd_DT)',
    }

    html_content = f"""
<!DOCTYPE html>
<html lang=\"ru\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Jobs vs Events Comparison</title>
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 16px; }}
    h2 {{ margin-top: 16px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }}
    th, td {{ border: 1px solid #eee; padding: 6px 8px; text-align: left; }}
    th {{ background: #fafafa; position: sticky; top: 0; }}
  </style>
</head>
<body>
  <h1>Сравнение метрик запросов и БД</h1>
  <p>Всего сопоставлено: <b>{len(results)}</b>. Валидных записей: <b>{len(valid_results)}</b>.</p>
  {('<p style=\"color:#dc2626\">Нет валидных строк — показаны все записи с пропусками.</p>' if not valid_results else '')}

  <div class=\"card\">
    <h2>Источники данных</h2>
    <p><strong>RequestSent_DT</strong> — берётся из журнала событий (STARTED events в requests_events.csv) или из timestamp_start_ms в requests.csv (момент отправки запроса Locust).</p>
    <p><strong>EvalStart_DT, EvalEnd_DT</strong> — берутся из ответа API /bps/call (поля started_at и finished_at из job), это данные из журнала процесса на сервере.</p>
    <p><strong>ResponseReceived_DT</strong> — берётся из timestamp_end_ms в requests.csv (момент получения ответа клиентом Locust).</p>
    <p><strong>Примечание:</strong> Если ResponseReceived_DT пустое, значит request_id из jobs_from_responses.csv не найден в requests.csv (возможна рассинхронизация или запрос не был залогирован Locust).</p>
  </div>

  <div class=\"card\">
    <h2>Графики по времени</h2>
    <p>Ось X — время (ResponseReceived_DT / EvalEnd_DT / EvalStart_DT / RequestSent_DT), ось Y — значение метрики.</p>
    <div style=\"position: relative; height: 600px; width: 100%;\">
      <canvas id=\"metricsChart\"></canvas>
    </div>
    <div style=\"margin-top: 20px; padding: 12px; background: #f9fafb; border-radius: 6px; font-size: 13px;\">
      <h3 style=\"margin-top: 0; font-size: 14px;\">Как вычисляются метрики:</h3>
      <ul style=\"margin: 8px 0; padding-left: 20px;\">
        <li><strong>RequestSent_DT</strong> — момент отправки запроса (из STARTED event или timestamp_start_ms в requests.csv)</li>
        <li><strong>EvalStart_DT</strong> — момент начала выполнения бизнес-логики (started_at из ответа API /bps/call)</li>
        <li><strong>EvalEnd_DT</strong> — момент окончания выполнения (finished_at из ответа API /bps/call)</li>
        <li><strong>ResponseReceived_DT</strong> — момент получения ответа клиентом (timestamp_end_ms из requests.csv)</li>
        <li><strong>Delay_ReqEval_ms</strong> = EvalStart_DT - RequestSent_DT (задержка от отправки до начала выполнения)</li>
        <li><strong>Duration_Eval_ms</strong> = EvalEnd_DT - EvalStart_DT (длительность выполнения бизнес-логики)</li>
        <li><strong>Delay_Eval_Resp_ms</strong> = ResponseReceived_DT - EvalEnd_DT (задержка от окончания выполнения до получения ответа)</li>
      </ul>
    </div>
  </div>

  <div class=\"card\">
    <h2>Выборочные записи (таблица)</h2>
    <p>Показано {len(filtered_for_table)} из {len(filtered)} записей. Полные данные доступны в CSV файлах.</p>
    <table>
      <thead>
        <tr>
          <th>#</th>
          {''.join([f'<th title="{html.escape(column_descriptions.get(col, col))}">{html.escape(col)}<br/><small style="font-weight: normal; color: #666;">{html.escape(column_descriptions.get(col, ""))}</small></th>' for col in table_cols])}
        </tr>
      </thead>
      <tbody>
        {''.join([f'<tr><td>{i+1}</td>' + ''.join([f'<td>{html.escape(str(r.get(col)) if r.get(col) is not None else "")}</td>' for col in table_cols]) + '</tr>' for i, r in enumerate(filtered_for_table)])}
      </tbody>
    </table>
  </div>

  <script>
    // Ждём загрузки Chart.js и DOM
    window.addEventListener('load', function() {{
      // Проверяем, что Chart.js загружен
      if (typeof Chart === 'undefined') {{
        console.error('Chart.js не загружен!');
        const chartContainer = document.getElementById('metricsChart').parentElement;
        chartContainer.innerHTML = '<p style="color: red; padding: 20px;">Ошибка: Chart.js не загружен. Проверьте подключение к интернету или откройте файл через веб-сервер.</p>';
        return;
      }}

      const labelsTime = {labels_js};
      const seriesDelayReqEval = {s_delay_reqeval_js};
      const seriesDurationEval = {s_duration_eval_js};
      const seriesDelayEvalResp = {s_delay_eval_resp_js};

      console.log('Данные для графика:', {{
        labels: labelsTime.length,
        delay_reqeval: seriesDelayReqEval.length,
        duration_eval: seriesDurationEval.length,
        delay_eval_resp: seriesDelayEvalResp.length
      }});

      // Проверяем, есть ли данные для графика
      if (!labelsTime || labelsTime.length === 0 || seriesDelayReqEval.length === 0) {{
        console.warn('Нет данных для построения графика');
        const chartContainer = document.getElementById('metricsChart').parentElement;
        chartContainer.innerHTML = '<p style="color: #666; padding: 20px; text-align: center;">Нет данных для построения графика. Запустите тест с данными.</p>';
        return;
      }}

      const canvas = document.getElementById('metricsChart');
      if (!canvas) {{
        console.error('Canvas элемент не найден!');
        return;
      }}

      const ctx = canvas.getContext('2d');
      if (!ctx) {{
        console.error('Не удалось получить контекст canvas!');
        return;
      }}

      try {{
        const metricsChart = new Chart(ctx, {{
          type: 'line',
          data: {{
            labels: labelsTime,
            datasets: [
              {{
                label: 'Delay_ReqEval_ms',
                data: seriesDelayReqEval,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.25,
                spanGaps: true,
              }},
              {{
                label: 'Duration_Eval_ms',
                data: seriesDurationEval,
                borderColor: '#16a34a',
                backgroundColor: 'rgba(22, 163, 74, 0.1)',
                tension: 0.25,
                spanGaps: true,
              }},
              {{
                label: 'Delay_Eval_Resp_ms',
                data: seriesDelayEvalResp,
                borderColor: '#dc2626',
                backgroundColor: 'rgba(220, 38, 38, 0.1)',
                tension: 0.25,
                spanGaps: true,
              }},
            ],
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{
              mode: 'nearest',
              intersect: false,
            }},
            plugins: {{
              legend: {{
                position: 'bottom',
              }},
              tooltip: {{
                callbacks: {{
                  title: (items) => {{
                    const i = items[0].dataIndex;
                    return labelsTime[i] || `#${{i + 1}}`;
                  }},
                }},
              }},
            }},
            scales: {{
              x: {{
                ticks: {{
                  maxRotation: 45,
                  minRotation: 0,
                  autoSkip: true,
                  maxTicksLimit: 12,
                }},
              }},
              y: {{
                title: {{
                  display: true,
                  text: 'ms',
                }},
              }},
            }},
          }},
        }});
        console.log('График создан успешно');
      }} catch (error) {{
        console.error('Ошибка при создании графика:', error);
        canvas.parentElement.innerHTML = '<p style="color: red; padding: 20px;">Ошибка при создании графика: ' + error.message + '</p>';
      }}
    }});
  </script>
</body>
</html>
"""

    report_path.write_text(html_content, encoding="utf-8")
    print(f"HTML report: {report_path}")

    # Сохраняем CSV: отфильтрованный и полный
    csv_full_path = out_dir / 'comparison_table_full.csv'
    csv_filtered_path = out_dir / 'comparison_table.csv'
    csv_cols_full = [
        'request_id',
        # Метрики по ТЗ
        'RequestSent_DT',
        'EvalStart_DT',
        'EvalEnd_DT',
        'ResponseReceived_DT',
        'Delay_ReqEval_ms',
        'Duration_Eval_ms',
        'Delay_Eval_Resp_ms',
    ]
    # Записываем CSV с BOM для правильного отображения в Excel и точкой с запятой как разделителем
    with csv_full_path.open('w', encoding='utf-8-sig', newline='') as cf_full:
        w_full = _csv.DictWriter(cf_full, fieldnames=csv_cols_full, delimiter=';')
        w_full.writeheader()
        for r in (valid_results or results):
            w_full.writerow({k: r.get(k) for k in csv_cols_full})
    # Filtered/output - записываем CSV с BOM для правильного отображения в Excel и точкой с запятой как разделителем
    with csv_filtered_path.open('w', encoding='utf-8-sig', newline='') as cf_f:
        w_f = _csv.DictWriter(cf_f, fieldnames=table_cols, delimiter=';')
        w_f.writeheader()
        for r in filtered:
            w_f.writerow({k: r.get(k) for k in table_cols})
    print(f"CSV (full): {csv_full_path}")
    print(f"CSV (filtered): {csv_filtered_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


