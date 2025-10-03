import csv
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from locust import HttpUser, task, between, events

# All paths are relative to this file folder
BASE_DIR = Path(__file__).parent.resolve()
CSV_DIR = BASE_DIR / "locust_logs"
CSV_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = CSV_DIR / "requests.csv"
REPORT_CSV_PATH = CSV_DIR / "requests_report.csv"
EVENTS_CSV_PATH = CSV_DIR / "requests_events.csv"

# Per-run responses CSV (timestamped)
RESPONSES_CSV_PATH = CSV_DIR / f"jobs_from_responses_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"


def ensure_csv_header(path: Path):
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_start_ms",
                "timestamp_start_iso",
                "timestamp_end_ms",
                "timestamp_end_iso",
                "response_time_ms",
                "method",
                "name",
                "path",
                "status_code",
                "success",
                "request_id",
                "exception",
            ])


def ensure_report_csv_header(path: Path):
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "request_date",
                "request_time",
                "response_date",
                "response_time",
                "status_code",
                "duration_ms",
                "request_id",
            ])


def ensure_events_csv_header(path: Path):
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "event_type",
                "event_date",
                "event_time",
                "status_code",
                "duration_ms",
                "request_id",
            ])


def ensure_responses_csv_header(path: Path):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "request_id",
            "object_id",
            "status",
            "path",
            "started_at",
            "finished_at",
            "job_duration",
            "job_uuid",
        ])


ensure_csv_header(CSV_PATH)
ensure_report_csv_header(REPORT_CSV_PATH)
ensure_events_csv_header(EVENTS_CSV_PATH)
ensure_responses_csv_header(RESPONSES_CSV_PATH)


class ApiUser(HttpUser):
    host = os.getenv("BASE_URL", "http://192.168.0.7:3333").rstrip("/")
    wait_time = between(1, 2)

    def on_start(self):
        self.default_headers = {"Content-Type": "application/json"}

    @task
    def call_bps(self):
        request_id = str(uuid.uuid4())
        path = "/api/ide/llda/branch/main/bps/call?path=test_que/test_1.df.json"

        start_dt_local = datetime.now().astimezone()
        start_dt_utc = datetime.now(timezone.utc)
        start_ms = int(start_dt_utc.timestamp() * 1000)
        started_date = start_dt_utc.strftime("%d.%m.%Y")
        started_time = f"{start_dt_utc.strftime('%H:%M:%S')}.{start_dt_utc.strftime('%f')[:5]}Z"
        object_id = f"{started_date} {started_time}"

        with EVENTS_CSV_PATH.open("a", newline="", encoding="utf-8") as fe:
            csv.writer(fe).writerow(["STARTED", started_date, started_time, "", "", request_id])

        payload = {"request_meta": {"object_id": object_id, "request_id": request_id, "tags": "string"}, "request_data": {}}
        with self.client.post(path, json=payload, headers=self.default_headers, name="POST /bps/call", catch_response=True) as resp:
            end_dt_local = datetime.now().astimezone()
            end_dt_utc = datetime.now(timezone.utc)
            end_ms = int(end_dt_utc.timestamp() * 1000)
            response_time_ms = end_ms - start_ms

            if 200 <= resp.status_code < 400:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

            # Save response JSON brief
            try:
                data = resp.json()
                job = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else {})
                if isinstance(job, dict):
                    with RESPONSES_CSV_PATH.open("a", newline="", encoding="utf-8") as fj:
                        csv.writer(fj).writerow([
                            job.get("request_id", request_id),
                            job.get("object_id", object_id),
                            job.get("status"),
                            job.get("path"),
                            job.get("started_at"),
                            job.get("finished_at"),
                            job.get("job_duration"),
                            job.get("job_uuid"),
                        ])
            except Exception:
                pass

            with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    start_ms,
                    start_dt_utc.isoformat(),
                    end_ms,
                    end_dt_utc.isoformat(),
                    response_time_ms,
                    "POST",
                    "POST /bps/call",
                    path,
                    resp.status_code,
                    200 <= resp.status_code < 400,
                    request_id,
                    "" if 200 <= resp.status_code < 400 else f"HTTP {resp.status_code}",
                ])

            req_date = start_dt_local.strftime("%d.%m.%Y")
            req_time = f"{start_dt_local.strftime('%H:%M:%S')}.{start_dt_local.strftime('%f')[:5]}"
            resp_date = end_dt_local.strftime("%d.%m.%Y")
            resp_time = f"{end_dt_local.strftime('%H:%M:%S')}.{end_dt_local.strftime('%f')[:5]}"
            with REPORT_CSV_PATH.open("a", newline="", encoding="utf-8") as f2:
                csv.writer(f2).writerow([req_date, req_time, resp_date, resp_time, resp.status_code, response_time_ms, request_id])

            finished_date = end_dt_utc.strftime("%d.%m.%Y")
            finished_time = f"{end_dt_utc.strftime('%H:%M:%S')}.{end_dt_utc.strftime('%f')[:5]}Z"
            with EVENTS_CSV_PATH.open("a", newline="", encoding="utf-8") as fe:
                csv.writer(fe).writerow(["FINISHED", finished_date, finished_time, resp.status_code, response_time_ms, request_id])


@events.request.add_listener
def _log_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    return

