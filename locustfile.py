import csv
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from locust import HttpUser, task, between, events


CSV_DIR = Path(os.getenv("LOCUST_CSV_DIR", "locust_logs"))
CSV_DIR.mkdir(exist_ok=True)
CSV_PATH = CSV_DIR / "requests.csv"
REPORT_CSV_PATH = CSV_DIR / "requests_report.csv"
EVENTS_CSV_PATH = CSV_DIR / "requests_events.csv"
RESPONSES_CSV_PATH = CSV_DIR / "jobs_from_responses.csv"
# Prefer REPORT_DIR if provided, else timestamped file to avoid accumulation across runs
report_dir_env = os.getenv("REPORT_DIR")
if report_dir_env:
    report_dir_path = Path(report_dir_env)
    report_dir_path.mkdir(parents=True, exist_ok=True)
    RESPONSES_CSV_PATH = report_dir_path / "jobs_from_responses.csv"
else:
    timestamp_name = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    RESPONSES_CSV_PATH = CSV_DIR / f"jobs_from_responses_{timestamp_name}.csv"
RAW_NDJSON_PATH = CSV_DIR / "raw_responses.ndjson"


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


ensure_csv_header(CSV_PATH)


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


ensure_report_csv_header(REPORT_CSV_PATH)


def ensure_events_csv_header(path: Path):
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "event_type",  # STARTED | FINISHED
                "event_date",
                "event_time",
                "status_code",
                "duration_ms",
                "request_id",
            ])


ensure_events_csv_header(EVENTS_CSV_PATH)


def ensure_responses_csv_header(path: Path):
    # Always (re)create for a clean run
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


ensure_responses_csv_header(RESPONSES_CSV_PATH)


class ApiUser(HttpUser):
    # Базовый хост можно переопределить переменной окружения BASE_URL
    host = os.getenv("BASE_URL", "http://192.168.0.7:3333").rstrip("/")
    wait_time = between(1, 2)

    def on_start(self):
        # Только базовые заголовки (без авторизации)
        self.default_headers = {"Content-Type": "application/json"}

    @task
    def call_bps(self):
        # Динамический request_id для корреляции с БД
        request_id = str(uuid.uuid4())

        # Параметры запроса
        path = "/api/ide/llda/branch/main/bps/call?path=test_que/test_1.df.json"

        # Время: локальное (для обратной совместимости object_id) и UTC (для корректной корреляции с БД)
        start_dt_local = datetime.now().astimezone()
        start_dt_utc = datetime.now(timezone.utc)
        start_ms = int(start_dt_utc.timestamp() * 1000)
        started_date = start_dt_utc.strftime("%d.%m.%Y")
        started_time = f"{start_dt_utc.strftime('%H:%M:%S')}.{start_dt_utc.strftime('%f')[:5]}Z"

        # object_id = та же самая метка времени старта
        object_id = f"{started_date} {started_time}"

        # МГНОВЕННАЯ запись события старта до отправки запроса
        with EVENTS_CSV_PATH.open("a", newline="", encoding="utf-8") as fe:
            writer_e = csv.writer(fe)
            writer_e.writerow([
                "STARTED",
                started_date,
                started_time,
                "",
                "",
                request_id,
            ])

        payload = {
            "request_meta": {
                "object_id": object_id,
                "request_id": request_id,
                "tags": "string",
            },
            "request_data": {},
        }
        with self.client.post(
            path,
            json=payload,
            headers=self.default_headers,
            name="POST /bps/call",
            catch_response=True,
        ) as resp:
            end_dt_local = datetime.now().astimezone()
            end_dt_utc = datetime.now(timezone.utc)
            end_ms = int(end_dt_utc.timestamp() * 1000)
            response_time_ms = end_ms - start_ms

            success = 200 <= resp.status_code < 400
            exception_text = ""
            if not success:
                exception_text = f"HTTP {resp.status_code}"
                resp.failure(exception_text)
            else:
                resp.success()

            # Парсим JSON и сохраняем ключевые поля из ответа
            try:
                data = resp.json()
                job = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else {})
                if isinstance(job, dict):
                    with RESPONSES_CSV_PATH.open("a", newline="", encoding="utf-8") as fj:
                        wj = csv.writer(fj)
                        wj.writerow([
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
                # Не JSON — пропускаем
                pass

            # Запись в CSV для последующей корреляции
            with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    start_ms,
                    start_dt_utc.isoformat(),
                    end_ms,
                    end_dt_utc.isoformat(),
                    response_time_ms,
                    "POST",
                    "POST /bps/call",
                    path,
                    resp.status_code,
                    success,
                    request_id,
                    exception_text,
                ])

            # Кастомный отчёт в требуемом формате
            # В отчёт по-прежнему пишем локальное время для читаемости
            req_date = start_dt_local.strftime("%d.%m.%Y")
            req_time = f"{start_dt_local.strftime('%H:%M:%S')}.{start_dt_local.strftime('%f')[:5]}"
            resp_date = end_dt_local.strftime("%d.%m.%Y")
            resp_time = f"{end_dt_local.strftime('%H:%M:%S')}.{end_dt_local.strftime('%f')[:5]}"
            with REPORT_CSV_PATH.open("a", newline="", encoding="utf-8") as f2:
                writer2 = csv.writer(f2)
                writer2.writerow([
                    req_date,
                    req_time,
                    resp_date,
                    resp_time,
                    resp.status_code,
                    response_time_ms,
                    request_id,
                ])

            # МГНОВЕННАЯ запись события завершения после получения ответа
            finished_date = end_dt_utc.strftime("%d.%m.%Y")
            finished_time = f"{end_dt_utc.strftime('%H:%M:%S')}.{end_dt_utc.strftime('%f')[:5]}Z"
            with EVENTS_CSV_PATH.open("a", newline="", encoding="utf-8") as fe:
                writer_e = csv.writer(fe)
                writer_e.writerow([
                    "FINISHED",
                    finished_date,
                    finished_time,
                    resp.status_code,
                    response_time_ms,
                    request_id,
                ])


# Дополнительно можно подписаться на события Locust (необязательно)
@events.request.add_listener
def _log_request(
    request_type: str,
    name: str,
    response_time: float,
    response_length: int,
    response,
    context,
    exception,
    **kwargs,
):
    # Этот listener фиксирует все запросы, если нужно централизованное логирование
    # Здесь можно добавить расширенный вывод, но CSV уже пишет задача выше.
    # Оставим хуком на будущее.
    return


