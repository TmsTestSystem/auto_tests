import csv
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from locust import HttpUser, task, between

# Base dir = folder of this file
BASE_DIR = Path(__file__).parent.resolve()
LOGS = BASE_DIR / "locust_logs"
LOGS.mkdir(parents=True, exist_ok=True)

# Per-run files
RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
CSV_REQUESTS = LOGS / f"requests_{RUN_TS}.csv"
CSV_EVENTS = LOGS / f"events_{RUN_TS}.csv"
CSV_RESPONSES = LOGS / f"jobs_from_responses_{RUN_TS}.csv"


def write_header(path: Path, header: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(header)


write_header(CSV_REQUESTS, [
    "timestamp_start_ms", "timestamp_start_iso", "timestamp_end_ms", "timestamp_end_iso",
    "response_time_ms", "method", "name", "path", "status_code", "success", "request_id", "exception",
])
write_header(CSV_EVENTS, ["event_type", "event_date", "event_time", "status_code", "duration_ms", "request_id"])
write_header(CSV_RESPONSES, ["request_id", "object_id", "status", "path", "started_at", "finished_at", "job_duration", "job_uuid"])


class ApiUser(HttpUser):
    host = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    wait_time = between(1, 2)

    def on_start(self):
        self.default_headers = {"Content-Type": "application/json"}

    @task
    def call_bps(self):
        request_id = str(uuid.uuid4())
        path = "/api/ide/llda/branch/main/bps/call?path=test_que/test_1.df.json"

        start_dt_utc = datetime.now(timezone.utc)
        start_ms = int(start_dt_utc.timestamp() * 1000)
        started_date = start_dt_utc.strftime("%d.%m.%Y")
        started_time = f"{start_dt_utc.strftime('%H:%M:%S')}.{start_dt_utc.strftime('%f')[:5]}Z"
        object_id = f"{started_date} {started_time}"

        # STARTED event
        with CSV_EVENTS.open("a", newline="", encoding="utf-8") as fe:
            csv.writer(fe).writerow(["STARTED", started_date, started_time, "", "", request_id])

        payload = {"request_meta": {"object_id": object_id, "request_id": request_id}, "request_data": {}}
        with self.client.post(path, json=payload, headers=self.default_headers, name="POST /bps/call", catch_response=True) as resp:
            end_dt_utc = datetime.now(timezone.utc)
            end_ms = int(end_dt_utc.timestamp() * 1000)
            response_time_ms = end_ms - start_ms

            if 200 <= resp.status_code < 400:
                resp.success()
                exc = ""
                success = True
            else:
                exc = f"HTTP {resp.status_code}"
                resp.failure(exc)
                success = False

            # Save brief JSON from response (if any)
            try:
                data = resp.json()
                job = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else {})
                if isinstance(job, dict):
                    with CSV_RESPONSES.open("a", newline="", encoding="utf-8") as fr:
                        csv.writer(fr).writerow([
                            job.get("request_id", request_id), job.get("object_id", object_id), job.get("status"),
                            job.get("path"), job.get("started_at"), job.get("finished_at"), job.get("job_duration"), job.get("job_uuid"),
                        ])
            except Exception:
                pass

            # Requests log
            with CSV_REQUESTS.open("a", newline="", encoding="utf-8") as fq:
                csv.writer(fq).writerow([
                    start_ms, start_dt_utc.isoformat(), end_ms, end_dt_utc.isoformat(), response_time_ms,
                    "POST", "POST /bps/call", path, resp.status_code, success, request_id, exc,
                ])

            # FINISHED event
            finished_date = end_dt_utc.strftime("%d.%m.%Y")
            finished_time = f"{end_dt_utc.strftime('%H:%M:%S')}.{end_dt_utc.strftime('%f')[:5]}Z"
            with CSV_EVENTS.open("a", newline="", encoding="utf-8") as fe:
                csv.writer(fe).writerow(["FINISHED", finished_date, finished_time, resp.status_code, response_time_ms, request_id])

