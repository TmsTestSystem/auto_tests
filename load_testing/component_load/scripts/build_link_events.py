"""
Вычисление времени стрелок между компонентами на основе последовательности выполнения.

Время стрелки = разница между окончанием одного компонента и началом следующего.
Компоненты выполняются последовательно (кроме flow и loop), поэтому мы можем
вычислить время стрелок напрямую из component_timings.csv.

Запуск:
  python build_link_events.py --report-dir path/to/report_dir

В report_dir должен лежать component_timings.csv (созданный locustfile.py или build_component_timings.py).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


def _to_int_us(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(float(value))
    except Exception:
        return None


def _us_to_iso(us: Optional[int]) -> str:
    if not us:
        return ""
    try:
        dt = datetime.fromtimestamp(us / 1_000_000.0, tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return ""


def load_jobs_from_responses_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        print(f"[LINK_EVENTS] WARNING: jobs_from_responses.csv не найден: {path}")
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_component_timings_csv(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Загружает component_timings.csv и группирует по request_id.
    Возвращает словарь: {request_id: [компоненты]}
    """
    components_by_request: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if not path.exists():
        return components_by_request
    
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            request_id = (row.get("request_id") or "").strip()
            if request_id:
                try:
                    start_us = int(row.get("start_us", 0) or 0)
                    end_us = int(row.get("end_us", 0) or 0)
                    components_by_request[request_id].append({
                        "component_key": row.get("component_key", ""),
                        "component_title": row.get("component_title", ""),
                        "component_title_base": row.get("component_title_base", ""),
                        "start_us": start_us,
                        "end_us": end_us,
                    })
                except (ValueError, TypeError):
                    continue
    
    # Сортируем компоненты по времени начала для каждого request_id
    for request_id in components_by_request:
        components_by_request[request_id].sort(key=lambda x: x.get("start_us", 0))
    
    return components_by_request


def build_link_events(report_dir: Path, project_code: str = "", branch: str = "master") -> Path:
    """
    Вычисляет время стрелок между компонентами на основе последовательности выполнения.
    Время стрелки = разница между окончанием одного компонента и началом следующего.
    """
    jobs_csv = report_dir / "jobs_from_responses.csv"
    component_timings_csv = report_dir / "component_timings.csv"
    out_csv = report_dir / "link_events.csv"

    print(f"[LINK_EVENTS] Начинаем обработку: report_dir={report_dir}, jobs_csv={jobs_csv}, component_timings_csv={component_timings_csv}")
    jobs = load_jobs_from_responses_csv(jobs_csv)
    if not jobs:
        print(f"[LINK_EVENTS] В {jobs_csv} нет записей, отчёт не будет создан.")
        return out_csv
    print(f"[LINK_EVENTS] Загружено {len(jobs)} jobs из {jobs_csv}")

    # Загружаем компоненты для вычисления времени стрелок
    components_by_request = load_component_timings_csv(component_timings_csv)
    print(f"[LINK_EVENTS] Загружено компонентов для {len(components_by_request)} запросов")
    
    # Создаём словарь request_id -> job_uuid для сопоставления
    request_id_to_job_uuid: Dict[str, str] = {}
    for j in jobs:
        request_id = (j.get("request_id") or "").strip()
        job_uuid = (j.get("job_uuid") or "").strip()
        if request_id and job_uuid:
            request_id_to_job_uuid[request_id] = job_uuid

    rows_out: List[Dict[str, Any]] = []
    
    # Вычисляем время стрелок на основе последовательности компонентов
    # Время стрелки = разница между окончанием одного компонента и началом следующего
    for request_id, components in components_by_request.items():
        if not components or len(components) < 2:
            continue
        
        job_uuid = request_id_to_job_uuid.get(request_id, "")
        
        # Сортируем компоненты по времени начала
        sorted_components = sorted(components, key=lambda c: c.get("start_us", 0))
        
        # Для каждой пары последовательных компонентов вычисляем время стрелки
        for i in range(len(sorted_components) - 1):
            from_comp = sorted_components[i]
            to_comp = sorted_components[i + 1]
            
            from_end_us = from_comp.get("end_us", 0)
            to_start_us = to_comp.get("start_us", 0)
            
            if from_end_us <= 0 or to_start_us <= 0:
                continue
            
            # Время стрелки = разница между концом from_component и началом to_component
            if to_start_us > from_end_us:
                duration_ms = (to_start_us - from_end_us) / 1000.0
                
                from_title = from_comp.get("component_title_base") or from_comp.get("component_title") or ""
                to_title = to_comp.get("component_title_base") or to_comp.get("component_title") or ""
                
                from_duration_ms = (from_end_us - from_comp.get("start_us", 0)) / 1000.0 if from_comp.get("start_us", 0) > 0 else None
                to_duration_ms = (to_comp.get("end_us", 0) - to_start_us) / 1000.0 if to_comp.get("end_us", 0) > to_start_us else None
                
                # Генерируем уникальный link_key для этой стрелки
                link_key = f"{from_comp.get('component_key', '')}_to_{to_comp.get('component_key', '')}"
                
                rows_out.append({
                    "request_id": request_id,
                    "job_uuid": job_uuid,
                    "link_key": link_key,
                    "path": "",  # Не используем path из link_event
                    "title": f"{from_title} → {to_title}",
                    "from_component": from_title,
                    "to_component": to_title,
                    "from_component_duration_ms": f"{from_duration_ms:.3f}" if from_duration_ms is not None else "",
                    "to_component_duration_ms": f"{to_duration_ms:.3f}" if to_duration_ms is not None else "",
                    "status_start": "computed",
                    "status_end": "computed",
                    "start_us": from_end_us,
                    "end_us": to_start_us,
                    "start_iso": _us_to_iso(from_end_us) if from_end_us else "",
                    "end_iso": _us_to_iso(to_start_us) if to_start_us else "",
                    "duration_ms": f"{duration_ms:.3f}",
                    "duration_from_events_ms": "",  # Не используем события
                    "parent_contexts_json": "",
                })

    # Стабильный порядок: по request_id, затем по времени начала стрелки
    def _sort_key(r: Dict[str, Any]):
        rid = r.get("request_id") or ""
        ts = r.get("start_us")
        try:
            ts_i = int(ts) if ts not in ("", None) else 0
        except Exception:
            ts_i = 0
        return (rid, ts_i)

    rows_out.sort(key=_sort_key)
    
    print(f"[LINK_EVENTS] Вычислено {len(rows_out)} стрелок на основе последовательности компонентов")
    if len(rows_out) == 0:
        print(f"[LINK_EVENTS] WARNING: Не найдено ни одной стрелки! Проверьте component_timings.csv")
        # Создаём пустой файл с заголовками
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "request_id", "job_uuid", "link_key", "path", "title",
                "from_component", "to_component",
                "from_component_duration_ms", "to_component_duration_ms",
                "status_start", "status_end",
                "start_us", "end_us", "start_iso", "end_iso",
                "duration_ms", "duration_from_events_ms", "parent_contexts_json",
            ])
        print(f"[LINK_EVENTS] Создан пустой файл {out_csv}")
        return out_csv

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "request_id",
                "job_uuid",
                "link_key",
                "path",
                "title",
                "from_component",
                "to_component",
                "from_component_duration_ms",
                "to_component_duration_ms",
                "status_start",
                "status_end",
                "start_us",
                "end_us",
                "start_iso",
                "end_iso",
                "duration_ms",
                "duration_from_events_ms",
                "parent_contexts_json",
            ]
        )
        for r in rows_out:
            w.writerow(
                [
                    r.get("request_id", ""),
                    r.get("job_uuid", ""),
                    r.get("link_key", ""),
                    r.get("path", ""),
                    r.get("title", ""),
                    r.get("from_component", ""),
                    r.get("to_component", ""),
                    r.get("from_component_duration_ms", ""),
                    r.get("to_component_duration_ms", ""),
                    r.get("status_start", ""),
                    r.get("status_end", ""),
                    r.get("start_us", ""),
                    r.get("end_us", ""),
                    r.get("start_iso", ""),
                    r.get("end_iso", ""),
                    r.get("duration_ms", ""),
                    r.get("duration_from_events_ms", ""),
                    r.get("parent_contexts_json", ""),
                ]
            )

    print(f"[LINK_EVENTS] Сохранено {len(rows_out)} link_event строк в {out_csv}")
    return out_csv


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(description="Вычисляет время стрелок между компонентами на основе последовательности выполнения")
    p.add_argument("--report-dir", type=str, required=True, help="Директория отчёта (с component_timings.csv и jobs_from_responses.csv)")
    p.add_argument("--project-code", type=str, default="", help="Код проекта (не используется, оставлено для совместимости)")
    p.add_argument("--branch", type=str, default="master", help="Ветка (не используется, оставлено для совместимости)")
    args = p.parse_args(argv)

    report_dir = Path(args.report_dir).resolve()
    build_link_events(report_dir, project_code=args.project_code, branch=args.branch)


if __name__ == "__main__":
    main()

