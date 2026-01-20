"""
Строит дополнительные CSV отчёты:
1) diagram_timings.csv — как растёт время выполнения диаграммы от запроса к запросу
2) component_gaps.csv — GAP (m) между соседними компонентами в порядке выполнения

Источник: component_timings.csv (создан build_component_timings.py)
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _to_float(s: Any) -> Optional[float]:
    try:
        if s is None or s == "":
            return None
        return float(s)
    except Exception:
        return None


def _to_int(s: Any) -> Optional[int]:
    try:
        if s is None or s == "":
            return None
        return int(float(s))
    except Exception:
        return None


def load_component_timings(csv_path: Path) -> List[Dict[str, Any]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"component_timings.csv не найден: {csv_path}")
    with csv_path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_diagram_timings(rows: List[Dict[str, Any]], out_path: Path) -> None:
    """
    diagram_duration_ms = (max(end_us) - min(start_us)) / 1000
    """
    by_req: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        rid = r.get("request_id") or ""
        if not rid:
            continue
        by_req[rid].append(r)

    # порядок запросов: как впервые встретились в файле
    req_order: List[str] = []
    seen = set()
    for r in rows:
        rid = r.get("request_id") or ""
        if rid and rid not in seen:
            seen.add(rid)
            req_order.append(rid)

    # Параллельно считаем сумму положительных GAP по каждому запросу
    gaps_sum_by_req: Dict[str, float] = defaultdict(float)
    for rid, items in by_req.items():
        # сортируем по start_us, чтобы считать соседние GAP
        items_sorted: List[Tuple[int, Dict[str, Any]]] = []
        for it in items:
            su = _to_int(it.get("start_us"))
            if isinstance(su, int):
                items_sorted.append((su, it))
        items_sorted.sort(key=lambda x: x[0])
        for idx in range(len(items_sorted) - 1):
            cur = items_sorted[idx][1]
            nxt = items_sorted[idx + 1][1]
            cur_end = _to_int(cur.get("end_us"))
            nxt_start = _to_int(nxt.get("start_us"))
            if not isinstance(cur_end, int) or not isinstance(nxt_start, int):
                continue
            gap_ms = (nxt_start - cur_end) / 1000.0
            if gap_ms > 0:
                gaps_sum_by_req[rid] += gap_ms

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "run_idx",
            "request_id",
            "job_uuid",
            "diagram_start_us",
            "diagram_end_us",
            "diagram_duration_ms",
            "gaps_sum_ms",
            "components_sum_ms",
            "gaps_share_pct",
            "components_count",
        ])
        for i, rid in enumerate(req_order, 1):
            items = by_req.get(rid, [])
            if not items:
                continue
            starts = [_to_int(x.get("start_us")) for x in items]
            ends = [_to_int(x.get("end_us")) for x in items]
            starts_i = [x for x in starts if isinstance(x, int)]
            ends_i = [x for x in ends if isinstance(x, int)]
            if not starts_i or not ends_i:
                continue
            start_us = min(starts_i)
            end_us = max(ends_i)
            duration_ms = (end_us - start_us) / 1000.0
            gaps_sum_ms = float(gaps_sum_by_req.get(rid, 0.0))
            components_sum_ms = max(0.0, duration_ms - gaps_sum_ms)
            gaps_share_pct = (gaps_sum_ms / duration_ms * 100.0) if duration_ms > 0 else 0.0
            job_uuid = items[0].get("job_uuid", "")
            w.writerow([
                i,
                rid,
                job_uuid,
                start_us,
                end_us,
                f"{duration_ms:.3f}",
                f"{gaps_sum_ms:.3f}",
                f"{components_sum_ms:.3f}",
                f"{gaps_share_pct:.2f}",
                len(items),
            ])


def build_component_gaps(rows: List[Dict[str, Any]], out_path: Path) -> None:
    """
    Для каждого request_id сортируем по start_us и пишем gap_ms между соседями:
      gap_ms = next.start_us - cur.end_us
    """
    by_req: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        rid = r.get("request_id") or ""
        if not rid:
            continue
        by_req[rid].append(r)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "request_id",
            "job_uuid",
            "from_component_title",
            "to_component_title",
            "from_end_us",
            "to_start_us",
            "gap_ms",
        ])

        for rid, items in by_req.items():
            items_sorted: List[Tuple[int, Dict[str, Any]]] = []
            for it in items:
                su = _to_int(it.get("start_us"))
                if isinstance(su, int):
                    items_sorted.append((su, it))
            items_sorted.sort(key=lambda x: x[0])

            for idx in range(len(items_sorted) - 1):
                cur = items_sorted[idx][1]
                nxt = items_sorted[idx + 1][1]
                cur_end = _to_int(cur.get("end_us"))
                nxt_start = _to_int(nxt.get("start_us"))
                if not isinstance(cur_end, int) or not isinstance(nxt_start, int):
                    continue
                gap_ms = (nxt_start - cur_end) / 1000.0
                w.writerow([
                    rid,
                    cur.get("job_uuid", ""),
                    cur.get("component_title", ""),
                    nxt.get("component_title", ""),
                    cur_end,
                    nxt_start,
                    f"{gap_ms:.3f}",
                ])


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(description="Строит отчёты diagram_timings.csv и component_gaps.csv")
    p.add_argument("--report-dir", required=True, help="Папка отчёта (содержит component_timings.csv)")
    args = p.parse_args(argv)
    report_dir = Path(args.report_dir).resolve()

    component_csv = report_dir / "component_timings.csv"
    rows = load_component_timings(component_csv)

    build_diagram_timings(rows, report_dir / "diagram_timings.csv")
    build_component_gaps(rows, report_dir / "component_gaps.csv")
    print(f"[DIAGRAM_AND_GAPS] Created: {report_dir / 'diagram_timings.csv'}")
    print(f"[DIAGRAM_AND_GAPS] Created: {report_dir / 'component_gaps.csv'}")


if __name__ == "__main__":
    main()

