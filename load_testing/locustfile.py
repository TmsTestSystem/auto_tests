import csv
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gevent.lock import Semaphore
from locust import HttpUser, task, between, events


CSV_DIR = Path(os.getenv("LOCUST_CSV_DIR", "locust_logs"))
CSV_DIR.mkdir(exist_ok=True)
REPORT_CSV_PATH = CSV_DIR / "requests_report.csv"
RESPONSES_CSV_PATH = CSV_DIR / "jobs_from_responses.csv"
# Предпочитаем REPORT_DIR, если задан, иначе файл с временной меткой для избежания накопления между запусками
report_dir_env = os.getenv("REPORT_DIR")
if report_dir_env:
    report_dir_path = Path(report_dir_env)
    report_dir_path.mkdir(parents=True, exist_ok=True)
    RESPONSES_CSV_PATH = report_dir_path / "jobs_from_responses.csv"
    # Используем REPORT_DIR для всех CSV файлов, чтобы каждый запуск имел свои файлы
    EVENTS_CSV_PATH = report_dir_path / "requests_events.csv"
    CSV_PATH = report_dir_path / "requests.csv"
else:
    timestamp_name = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    RESPONSES_CSV_PATH = CSV_DIR / f"jobs_from_responses_{timestamp_name}.csv"
    EVENTS_CSV_PATH = CSV_DIR / "requests_events.csv"
    CSV_PATH = CSV_DIR / "requests.csv"
RAW_NDJSON_PATH = CSV_DIR / "raw_responses.ndjson"

# Опциональный сбор метрик по компонентам через /api/events/{job_uuid}
COLLECT_COMPONENT_EVENTS = os.getenv("COLLECT_COMPONENT_EVENTS", "false").lower() in ("1", "true", "yes")
DEBUG_COMPONENT_EVENTS = os.getenv("DEBUG_COMPONENT_EVENTS", "false").lower() in ("1", "true", "yes")
COMPONENTS_CSV_PATH = (Path(report_dir_env) if report_dir_env else CSV_DIR) / "component_timings.csv"
EVENTS_ERRORS_CSV_PATH = (Path(report_dir_env) if report_dir_env else CSV_DIR) / "events_fetch_errors.csv"

# Глобальный лимит по количеству запросов (0 = без лимита)
TOTAL_REQUESTS_LIMIT = int(os.getenv("TOTAL_REQUESTS", "0") or "0")
_requests_done = 0
_requests_done_lock: Semaphore = Semaphore()

# Импортируем auth utils из корня репозитория (locustfile запускается из поддиректории)
REPO_ROOT = Path(__file__).resolve().parents[1]  # .../auto-test2_0
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
try:
    from utils.auth_utils import get_auth_cookies, get_api_base_url  # type: ignore  # noqa: E402
except Exception:
    get_auth_cookies = None  # type: ignore[assignment]
    get_api_base_url = None  # type: ignore[assignment]


def ensure_csv_header(path: Path):
    # Всегда пересоздаём файл для чистого запуска (как для events и responses CSV)
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
    # Всегда пересоздаём файл для чистого запуска (как для responses CSV)
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
    # Всегда пересоздаём для чистого запуска
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


def ensure_components_csv_header(path: Path):
    if not COLLECT_COMPONENT_EVENTS:
        return
    # Всегда пересоздаём для чистого запуска в рамках REPORT_DIR
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "request_id",
            "job_uuid",
            "component_key",
            "component_title",
            "component_type",
            "start_us",
            "end_us",
            "duration_ms",
            "gap_from_prev_ms",
        ])


ensure_components_csv_header(COMPONENTS_CSV_PATH)


def ensure_events_errors_csv_header(path: Path):
    if not COLLECT_COMPONENT_EVENTS:
        return
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "request_id",
                "job_uuid",
                "host",
                "error_type",
                "status_code",
                "url",
                "response_text",
            ])


ensure_events_errors_csv_header(EVENTS_ERRORS_CSV_PATH)

# Параметры проекта/процесса для нагрузочного теста передаются через env,
# чтобы run.py мог создавать проект динамически и импортировать zip.
LOAD_PROJECT_CODE = os.getenv("LOAD_PROJECT_CODE", "llda")
LOAD_BRANCH = os.getenv("LOAD_BRANCH", "main")
LOAD_PROCESS_PATH = os.getenv("LOAD_PROCESS_PATH", "test_que/test_1.df.json")


class ApiUser(HttpUser):
    # Базовый хост можно переопределить переменной окружения BASE_URL
    host = os.getenv("BASE_URL", "http://192.168.0.7:3333").rstrip("/")
    wait_time = between(1, 2)

    def on_start(self):
        # Только базовые заголовки (без авторизации)
        self.default_headers = {"Content-Type": "application/json"}
        self._auth_cookies = None
        if COLLECT_COMPONENT_EVENTS and callable(get_auth_cookies):
            try:
                self._auth_cookies = get_auth_cookies()
            except Exception:
                # Если стенд не требует авторизации на /api/events, продолжим без cookies
                self._auth_cookies = None

    @task
    def call_bps(self):
        # Динамический request_id для корреляции с БД
        request_id = str(uuid.uuid4())

        # Параметры запроса: используем динамический проект/ветку/путь процесса
        path = f"/api/ide/{LOAD_PROJECT_CODE}/branch/{LOAD_BRANCH}/bps/call?path={LOAD_PROCESS_PATH}"

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
                "object_id": object_id,  # Динамическая метка времени
                "request_id": request_id,  # UUID
                "tags": "string",
            },
            "request_data": {
                "amount_requested": {
                    "currency_code": "RUB",
                    "value": 12,
                },
                "auto": {
                    "VIN": "string",
                    "is_new": True,
                    "is_used": True,
                    "owner": {
                        "firstname": "string",
                        "lastname": "string",
                        "middlename": "string",
                        "passport": {
                            "number": "string",
                            "series": "string",
                        },
                    },
                },
                "co_issuers": [
                    {
                        "firstname": "string",
                        "lastname": "string",
                        "middlename": "string",
                        "passport": {
                            "number": "string",
                            "series": "string",
                        },
                    }
                ],
                "initial_payment": {
                    "currency_code": "RUB",
                    "value": 31,
                },
                "issuer": {
                    "firstname": "string",
                    "lastname": "string",
                    "middlename": "string",
                    "passport": {
                        "number": "string",
                        "series": "string",
                    },
                },
            },
        }
        with self.client.post(
            path,
            json=payload,
            headers=self.default_headers,
            name="POST /bps/call",
            catch_response=True,
            verify=False,
        ) as resp:
            end_dt_local = datetime.now().astimezone()
            end_dt_utc = datetime.now(timezone.utc)
            end_ms = int(end_dt_utc.timestamp() * 1000)
            response_time_ms = end_ms - start_ms

            success = 200 <= resp.status_code < 400
            exception_text = ""
            if not success:
                exception_text = f"HTTP {resp.status_code}"
                # Логируем тело ответа при ошибке для отладки
                try:
                    error_body = resp.text[:1000]  # Первые 1000 символов
                    # Записываем в файл для надёжности
                    error_log_path = CSV_DIR / "error_responses.txt"
                    with error_log_path.open("a", encoding="utf-8") as ef:
                        ef.write(f"\n[{datetime.now(timezone.utc).isoformat()}] Status {resp.status_code} for {path}\n")
                        ef.write(f"Body: {error_body}\n")
                        ef.write("-" * 80 + "\n")
                    # Также в stdout для быстрого просмотра
                    print(f"[ERROR] Response body (status {resp.status_code}): {error_body}")
                except Exception as log_err:
                    print(f"[ERROR] Failed to log error response: {log_err}")
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

                    # Дополнительно: по job_uuid забираем события и считаем метрики компонентов
                    if COLLECT_COMPONENT_EVENTS:
                        job_uuid = job.get("job_uuid")
                        if job_uuid:
                            try:
                                self._collect_component_timings(
                                    request_id=job.get("request_id", request_id),
                                    job_uuid=job_uuid,
                                )
                            except Exception as e:
                                # Не валим нагрузку из-за проблем сбора метрик, но логируем причину в отдельный CSV
                                status_code = getattr(e, "_events_status_code", "")
                                url = getattr(e, "_events_url", "")
                                body = getattr(e, "_events_body", "")
                                with EVENTS_ERRORS_CSV_PATH.open("a", newline="", encoding="utf-8") as fe:
                                    we = csv.writer(fe)
                                    we.writerow([
                                        job.get("request_id", request_id),
                                        job_uuid,
                                        getattr(self, "host", ""),
                                        type(e).__name__,
                                        status_code,
                                        url,
                                        (str(body)[:2000] if body else str(e)[:2000]),
                                    ])
                                if DEBUG_COMPONENT_EVENTS:
                                    print(f"[COMPONENT_EVENTS_ERROR] request_id={job.get('request_id', request_id)} job_uuid={job_uuid} err={e}")
            except Exception:
                # Не JSON — пропускаем
                pass

            # Запись в CSV для последующей корреляции данных
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

            # Лимитируем общее количество запросов, если TOTAL_REQUESTS_LIMIT > 0
            if TOTAL_REQUESTS_LIMIT > 0 and self.environment and self.environment.runner:
                global _requests_done
                with _requests_done_lock:
                    _requests_done += 1
                    if _requests_done >= TOTAL_REQUESTS_LIMIT:
                        print(f"[LOCUST] TOTAL_REQUESTS_LIMIT={TOTAL_REQUESTS_LIMIT} достигнут, останавливаем раннер")
                        events.request.fire(
                            request_type="STOP",
                            name="Locust Stop",
                            response_time=0,
                            response_length=0,
                            response=None,
                            context=None,
                            exception=None,
                        )
                        self.environment.runner.quit()


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
    # Здесь можно добавить расширенный вывод, но CSV уже пишет задача выше
    # Оставляем хуком на будущее
    return


def _to_int_us(value: Any) -> Optional[int]:
    """
    inserted_timestamp приходит как float (микросекунды от epoch).
    Приводим к int microseconds.
    """
    try:
        if value is None:
            return None
        # value может быть float, int или строка
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
    для component_event.
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
            # берём первый старт
            if rec["start_us"] is None or ts_us < rec["start_us"]:
                rec["start_us"] = ts_us
        elif status == "done":
            # берём последний end
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
    # сортируем по старту, чтобы посчитать интервалы между компонентами
    rows.sort(key=lambda r: r[3])
    return rows


def _gap_ms(prev_end_us: Optional[int], cur_start_us: int) -> Optional[float]:
    if prev_end_us is None:
        return None
    return (cur_start_us - prev_end_us) / 1000.0


def _api_base_from_host(host: str) -> str:
    # host уже содержит base url вида http://192.168.0.7:3333
    return host.rstrip("/")


def _events_url(host: str, job_uuid: str) -> str:
    return f"{_api_base_from_host(host)}/api/events/{job_uuid}"


def _write_component_rows(request_id: str, job_uuid: str, rows: List[Tuple[str, str, str, int, int, float]]) -> None:
    if not COLLECT_COMPONENT_EVENTS:
        return
    prev_end: Optional[int] = None
    with COMPONENTS_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for (key, title, ctype, start_us, end_us, duration_ms) in rows:
            gap = _gap_ms(prev_end, start_us)
            w.writerow([
                request_id,
                job_uuid,
                key,
                title,
                ctype,
                start_us,
                end_us,
                f"{duration_ms:.3f}",
                ("" if gap is None else f"{gap:.3f}"),
            ])
            prev_end = end_us


def _fetch_events(host: str, job_uuid: str, cookies=None) -> Any:
    """
    Запрос events делаем через requests, потому что locust self.client заточен под base_url и может не иметь cookies.
    """
    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    url = _events_url(host, job_uuid)
    resp = requests.get(url, cookies=cookies, verify=False, timeout=60)
    if not resp.ok:
        # Дадим максимум информации для диагностики (на тестовых стендах часто 401/403)
        err = RuntimeError(f"events fetch failed: status={resp.status_code}, url={url}, body={resp.text[:2000]}")
        setattr(err, "_events_status_code", resp.status_code)
        setattr(err, "_events_url", url)
        setattr(err, "_events_body", resp.text)
        raise err
    return resp.json()


def _noop(*args, **kwargs):
    return None


# Вешаем методы на класс, чтобы можно было вызывать self._collect_component_timings
def _collect_component_timings(self: ApiUser, request_id: str, job_uuid: str) -> None:  # type: ignore[name-defined]
    """
    Получаем события по job_uuid и несколько раз пробуем,
    т.к. на боевых стендах компоненты в /api/events/{job_uuid}
    могут появляться с небольшой задержкой после завершения джоба.
    """
    max_attempts = int(os.getenv("COMP_EVENTS_RETRY_ATTEMPTS", "3") or "3")
    delay_sec = float(os.getenv("COMP_EVENTS_RETRY_DELAY", "0.5") or "0.5")

    attempts = 0
    rows: List[Tuple[str, str, str, int, int, float]] = []

    while attempts < max_attempts and not rows:
        attempts += 1
        payload = _fetch_events(self.host, job_uuid, cookies=getattr(self, "_auth_cookies", None))
        events = _extract_events(payload)
        rows = _compute_component_rows(events)

        if rows:
            break

        # Если компоненты ещё не успели появиться в events — подождём и попробуем ещё раз
        if attempts < max_attempts:
            if DEBUG_COMPONENT_EVENTS:
                print(f"[COMP_EVENTS_RETRY] job_uuid={job_uuid} attempt={attempts} no component rows yet, sleep {delay_sec}s")
            time.sleep(delay_sec)

    if not rows:
        if DEBUG_COMPONENT_EVENTS:
            print(f"[COMP_EVENTS_RETRY] job_uuid={job_uuid} no component rows after {max_attempts} attempts")
        return

    _write_component_rows(request_id, job_uuid, rows)


setattr(ApiUser, "_collect_component_timings", _collect_component_timings)

