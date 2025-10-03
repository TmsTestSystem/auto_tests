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


# Determine base directory (can be overridden for load/ usage)
base_dir_env = os.getenv('BASE_DIR')
if base_dir_env:
    BASE_ROOT = Path(base_dir_env)
else:
    BASE_ROOT = Path(__file__).parent


def load_started_events(events_csv_path: Path) -> Dict[str, dt.datetime]:
    """Load STARTED events from requests_events.csv and map request_id -> datetime (naive UTC).
    Time format in CSV: date=DD.MM.YYYY, time=HH:MM:SS.fffff (optionally with trailing 'Z').
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
            # Naive datetime (treat as UTC for comparison)
            started_dt = dt.datetime.strptime(
                f"{event_date} {time_no_z}", "%d.%m.%Y %H:%M:%S.%f"
            )
            request_id_to_started[rid] = started_dt
    return request_id_to_started


def load_jobs(jobs_json_path: Path) -> List[Dict[str, Any]]:
    """Load jobs list from jobs.json where API may return array or object with items."""
    text = jobs_json_path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "items" in data:
            return list(data["items"])  # type: ignore[index]
        if isinstance(data, list):
            return list(data)
    except Exception:
        pass

    # Fallback: extract the first JSON array from the text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    return []


def load_jobs_from_responses_csv(path: Path) -> List[Dict[str, Any]]:
    """Load jobs from locust-captured CSV (jobs_from_responses.csv)."""
    jobs: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        for row in reader:
            # Normalize to API-like schema
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
) -> List[Dict[str, Any]]:
    """For each matching request_id compute:
    - delta_started_at_vs_object_id_ms
    - delta_finished_at_vs_response_end_ms
    - delta_job_duration_vs_object_to_response_end_ms (job_duration - (response_end - object_id))
    Also keep previous deltas for reference.
    Returns list of dict rows for easy printing/analysis.
    """
    results: List[Dict[str, Any]] = []
    for job in jobs:
        rid = job.get("request_id")
        obj = job.get("object_id")  # "DD.MM.YYYY HH:MM:SS.fffff"
        sa = job.get("started_at")  # ISO UTC string
        fa = job.get("finished_at")  # ISO UTC string
        job_duration = job.get("job_duration")  # already in ms per API
        if not rid or not obj or not sa or rid not in started_map or not fa:
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

        # Normalize started_at/finished_at to naive UTC for difference
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

        # Locust metrics
        rm = req_metrics.get(rid)
        response_time_ms = rm.get("response_time_ms", -1) if rm else -1
        end_ms = rm.get("timestamp_end_ms") if rm else None

        # Compute response_end time if available
        response_end_dt = None
        if end_ms is not None:
            # end_ms is epoch ms UTC
            response_end_dt = dt.datetime.utcfromtimestamp(end_ms / 1000.0)

        # Derived comparisons per requirements
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

        results.append(
            {
                "request_id": rid,
                "delta_started_at_vs_event_ms": d_started_ms,
                "delta_object_id_vs_event_ms": d_object_ms,
                "locust_response_time_ms": response_time_ms,
                "db_duration_ms": db_duration_ms,
                "delta_resp_vs_db_ms": (response_time_ms - db_duration_ms) if response_time_ms >= 0 else None,
                "delta_started_at_vs_object_id_ms": delta_started_at_vs_object_id_ms,
                "delta_finished_at_vs_response_end_ms": delta_finished_at_vs_response_end_ms,
                "delta_object_id_to_response_end_ms": delta_object_id_to_response_end_ms,
                "delta_job_duration_vs_object_to_response_end_ms": delta_job_duration_vs_object_to_response_end_ms,
                # raw values for the report
                "event": ev_dt.isoformat(sep=" "),
                "object_id": obj_dt.isoformat(sep=" "),
                "started_at": sa,
                "finished_at": fa,
                "response_end": (response_end_dt.isoformat(sep=" ") if response_end_dt is not None else None),
                "job_duration": (int(job_duration) if isinstance(job_duration, str) and job_duration.isdigit() else job_duration),
            }
        )

    # Sort by absolute delta vs started_at
    results.sort(key=lambda x: abs(x["delta_started_at_vs_event_ms"]))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate comparison report with optional filtering/sampling")
    parser.add_argument("--delta-range-ms", nargs=2, type=int, metavar=("MIN","MAX"), help="Filter by delta_started_at_vs_object_id_ms in [MIN, MAX]")
    parser.add_argument("--abs-delta-top", type=int, default=None, help="Keep top-N by |delta_started_at_vs_object_id_ms|")
    parser.add_argument("--bucket-ms", type=int, default=None, help="Bucket size in ms for delta_started_at_vs_object_id_ms")
    parser.add_argument("--samples-per-bucket", type=int, default=3, help="Samples per bucket to keep (with --bucket-ms)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows in table/filtered CSV")
    parser.add_argument("--columns", type=str, default=None, help="Comma-separated list of columns to include in table/CSV")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = BASE_ROOT
    # Prefer explicit events file; support legacy/alt naming
    events_csv_candidates = [
        root / "locust_logs" / "requests_events.csv",
        root / "locust_logs" / "requests_data_time.csv",
    ]
    events_csv = next((p for p in events_csv_candidates if p.exists()), events_csv_candidates[0])
    # Requests CSV: prefer the latest timestamped variant requests_YYYYMMDD_HHMMSS.csv, fallback to requests.csv
    requests_dir = root / "locust_logs"
    ts_req_candidates = sorted(
        (requests_dir.glob("requests_*.csv") if requests_dir.exists() else []),
        key=lambda x: x.stat().st_mtime
    )
    requests_csv = ts_req_candidates[-1] if ts_req_candidates else (requests_dir / "requests.csv")
    jobs_json = root / "jobs.json"
    # Prefer per-run responses CSV
    responses_csv = None
    env_dir = os.getenv('REPORT_DIR')
    if env_dir:
        p = Path(env_dir) / 'jobs_from_responses.csv'
        if p.exists():
            responses_csv = p
    if responses_csv is None:
        # Try latest timestamped file in BASE_ROOT/locust_logs
        candidates = sorted((root / 'locust_logs').glob('jobs_from_responses_*.csv'), key=lambda x: x.stat().st_mtime)
        if candidates:
            responses_csv = candidates[-1]
    if responses_csv is None:
        # Try legacy single file in BASE_ROOT
        p = root / 'locust_logs' / 'jobs_from_responses.csv'
        if p.exists():
            responses_csv = p
    if responses_csv is None:
        # Try parent project locust_logs (when running under load/)
        parent_logs = root.parent / 'locust_logs'
        candidates = sorted(parent_logs.glob('jobs_from_responses_*.csv'), key=lambda x: x.stat().st_mtime) if parent_logs.exists() else []
        if candidates:
            responses_csv = candidates[-1]
        else:
            p = parent_logs / 'jobs_from_responses.csv'
            if p.exists():
                responses_csv = p

    if responses_csv:
        print(f"Using responses CSV: {responses_csv}")

    if not events_csv.exists():
        print(f"No events CSV found: {events_csv}")
    if (responses_csv is None or not responses_csv.exists()) and not jobs_json.exists():
        print(f"No jobs sources found. Missing: {jobs_json} and {responses_csv}")
        return 1

    # Load response metrics from requests.csv by request_id and by derived object_id
    req_metrics: Dict[str, Dict[str, int]] = {}
    objid_to_endms: Dict[str, int] = {}
    # If we have responses, collect their request_ids to restrict join
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
            # Find indices
            try:
                idx_request_id = header.index("request_id")
                idx_response_time = header.index("response_time_ms")
                idx_start_ms = header.index("timestamp_start_ms")
                idx_end_ms = header.index("timestamp_end_ms")
            except ValueError:
                idx_request_id = idx_response_time = idx_start_ms = idx_end_ms = -1
            if idx_request_id >= 0 and idx_response_time >= 0 and idx_end_ms >= 0:
                for row in reader:
                    if not row or len(row) <= max(idx_request_id, idx_response_time, idx_end_ms):
                        continue
                    rid = row[idx_request_id]
                    if response_request_ids and rid not in response_request_ids:
                        continue
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
                    # Derive object_id string from start_ms to allow fallback join
                    if start_ms is not None:
                        try:
                            start_dt_utc = dt.datetime.utcfromtimestamp(start_ms / 1000.0)
                            obj_date = start_dt_utc.strftime("%d.%m.%Y")
                            obj_time = f"{start_dt_utc.strftime('%H:%M:%S')}.{start_dt_utc.strftime('%f')[:5]}Z"
                            object_id_str = f"{obj_date} {obj_time}"
                            objid_to_endms[object_id_str] = end_ms
                        except Exception:
                            pass

    # Build started_map:
    # - Prefer STARTED events from requests_events.csv when present
    # - If missing, derive from requests.csv timestamp_start_ms (UTC epoch ms)
    if events_csv.exists():
        started_map = load_started_events(events_csv)
    else:
        started_map = {}
        # Primary: derive from req_metrics (already parsed from requests.csv)
        if req_metrics:
            for rid, m in req_metrics.items():
                start_ms = m.get("timestamp_start_ms")
                if start_ms is None:
                    continue
                try:
                    started_map[rid] = dt.datetime.utcfromtimestamp(start_ms / 1000.0)
                except Exception:
                    continue
        # Fallback: read requests.csv directly if still empty
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
        print(f"Derived STARTED map from requests.csv: {len(started_map)} records")
    # Prefer CSV collected from responses; fallback to jobs.json
    if responses_csv:
        jobs = load_jobs_from_responses_csv(responses_csv)
        print(f"Loaded jobs from responses CSV: {len(jobs)} records")
    else:
        jobs = load_jobs(jobs_json)
        print(f"Loaded jobs from jobs.json: {len(jobs)} records")
    results = compare_times(started_map, jobs, req_metrics)

    # Diagnostics: how many rows have response_end present
    has_resp_end = sum(1 for r in results if r.get("delta_finished_at_vs_response_end_ms") is not None)
    print(f"matched={len(results)} | with_response_end={has_resp_end}")
    for r in results[:20]:
        parts = [
            f"request_id={r['request_id']}",
            f"delta_started_at_vs_object_id_ms={r['delta_started_at_vs_object_id_ms']}",
            f"delta_finished_at_vs_response_end_ms={r['delta_finished_at_vs_response_end_ms']}",
            f"delta_job_duration_vs_object_to_response_end_ms={r['delta_job_duration_vs_object_to_response_end_ms']}",
            f"locust_response_time_ms={r['locust_response_time_ms']}",
            f"db_duration_ms={r['db_duration_ms']}",
            f"delta_resp_vs_db_ms={r['delta_resp_vs_db_ms']}",
            f"event={r['event']}",
            f"object_id={r['object_id']}",
            f"started_at={r['started_at']}",
            f"finished_at={r['finished_at']}",
        ]
        print(" | ".join(parts))

    # Keep only rows where response_end and job_duration based deltas are present
    valid_results = [
        r for r in results
        if r["delta_finished_at_vs_response_end_ms"] is not None
        and r["delta_object_id_to_response_end_ms"] is not None
        and r["delta_job_duration_vs_object_to_response_end_ms"] is not None
    ]
    used_for_graphs = valid_results if valid_results else results

    # Apply optional filtering/sampling
    filtered: List[Dict[str, Any]] = list(used_for_graphs)
    # Range filter on delta_started_at_vs_object_id_ms
    if args.delta_range_ms is not None:
        min_d, max_d = args.delta_range_ms
        filtered = [r for r in filtered if r.get("delta_started_at_vs_object_id_ms") is not None and min_d <= r["delta_started_at_vs_object_id_ms"] <= max_d]
    # Top-N by absolute delta
    if args.abs_delta_top is not None and args.abs_delta_top > 0:
        filtered = sorted(filtered, key=lambda r: abs(r.get("delta_started_at_vs_object_id_ms") or 0), reverse=True)[: args.abs_delta_top]
    # Bucketing by delta and sampling
    if args.bucket_ms is not None and args.bucket_ms > 0:
        from collections import defaultdict
        buckets: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for r in filtered:
            d = r.get("delta_started_at_vs_object_id_ms")
            if d is None:
                continue
            b = (d // args.bucket_ms) * args.bucket_ms
            if len(buckets[b]) < max(1, args.samples_per_bucket):
                buckets[b].append(r)
        # Flatten in bucket order
        filtered = []
        for b in sorted(buckets.keys()):
            filtered.extend(buckets[b])
    # Limit rows
    if args.limit is not None and args.limit > 0:
        filtered = filtered[: args.limit]

    # Output directory marked by date-time or provided via env
    env_dir = os.getenv('REPORT_DIR')
    if env_dir:
        out_dir = Path(env_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        timestamp_str = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        out_dir = BASE_ROOT / 'reports' / timestamp_str
        out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Report directory: {out_dir}")

    # Build simple HTML report (table only)
    report_path = out_dir / 'comparison_report.html'
    labels = [html.escape(r['request_id']) for r in filtered]
    ds_started_vs_obj = [r.get('delta_started_at_vs_object_id_ms') for r in filtered]
    ds_finished_vs_resp = [r.get('delta_finished_at_vs_response_end_ms') for r in filtered]
    ds_jobdur_vs_obj2resp = [r.get('delta_job_duration_vs_object_to_response_end_ms') for r in filtered]

    # Keep only first N to avoid huge pages
    N = 500
    labels = labels[:N]
    ds_started_vs_obj = ds_started_vs_obj[:N]
    ds_finished_vs_resp = ds_finished_vs_resp[:N]
    ds_jobdur_vs_obj2resp = ds_jobdur_vs_obj2resp[:N]

    # Choose columns
    default_cols = [
        'request_id','delta_started_at_vs_object_id_ms','delta_finished_at_vs_response_end_ms',
        'delta_job_duration_vs_object_to_response_end_ms','started_at','object_id','finished_at','response_end','job_duration'
    ]
    table_cols = [c.strip() for c in args.columns.split(',')] if args.columns else default_cols

    html_content = f"""
<!DOCTYPE html>
<html lang=\"ru\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Jobs vs Events Comparison</title>
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
    <h2>Все записи (таблица)</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          {''.join([f'<th>{html.escape(col)}</th>' for col in table_cols])}
        </tr>
      </thead>
      <tbody>
        {''.join([f'<tr><td>{i+1}</td>' + ''.join([f'<td>{html.escape(str(r.get(col)) if r.get(col) is not None else "")}</td>' for col in table_cols]) + '</tr>' for i, r in enumerate(filtered)])}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

    report_path.write_text(html_content, encoding="utf-8")
    print(f"HTML report: {report_path}")

    # Save CSVs: filtered and full
    csv_full_path = out_dir / 'comparison_table_full.csv'
    csv_filtered_path = out_dir / 'comparison_table.csv'
    csv_cols_full = [
        'request_id','delta_started_at_vs_object_id_ms','delta_finished_at_vs_response_end_ms',
        'delta_job_duration_vs_object_to_response_end_ms','locust_response_time_ms','db_duration_ms','delta_resp_vs_db_ms',
        'started_at','object_id','finished_at','response_end','job_duration'
    ]
    with csv_full_path.open('w', encoding='utf-8', newline='') as cf_full:
        w_full = _csv.DictWriter(cf_full, fieldnames=csv_cols_full)
        w_full.writeheader()
        for r in (valid_results or results):
            w_full.writerow({k: r.get(k) for k in csv_cols_full})
    # Filtered/output
    with csv_filtered_path.open('w', encoding='utf-8', newline='') as cf_f:
        w_f = _csv.DictWriter(cf_f, fieldnames=table_cols)
        w_f.writeheader()
        for r in filtered:
            w_f.writerow({k: r.get(k) for k in table_cols})
    print(f"CSV (full): {csv_full_path}")
    print(f"CSV (filtered): {csv_filtered_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


