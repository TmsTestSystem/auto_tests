import csv
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gevent
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
_stop_requested = False
_stop_lock: Semaphore = Semaphore()
_quit_scheduled = False
_attempts_started = 0
_attempts_completed = 0
_in_flight = 0

# Ожидаемое количество компонентных событий на один job_uuid.
# Вычисляется по первому успешно собранному job и далее используется
# как "эталон" для остальных (мы ждём, пока не наберём столько же).
_expected_components_per_job: Optional[int] = None

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
        # Проверяем флаг остановки перед выполнением задачи
        global _stop_requested, _attempts_started, _in_flight
        with _stop_lock:
            if _stop_requested:
                # Прерываем выполнение задачи, если запрошена остановка
                return

        # Жёсткий лимит по количеству попыток (attempts).
        # ВАЖНО: инкрементируем ДО отправки запроса, чтобы никогда не уйти в "+1" при нескольких пользователях.
        if TOTAL_REQUESTS_LIMIT > 0:
            with _requests_done_lock:
                if _attempts_started >= TOTAL_REQUESTS_LIMIT:
                    return
                _attempts_started += 1
                _in_flight += 1
                # Как только набрали лимит по начатым попыткам — запрещаем старт новых задач
                if _attempts_started >= TOTAL_REQUESTS_LIMIT:
                    with _stop_lock:
                        _stop_requested = True
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
        resp = None
        max_retries = 2  # Максимум 2 повтора для 422 ошибок
        retry_delay = 0.5  # Задержка между повторами (секунды)
        
        try:
            for attempt in range(max_retries + 1):
                try:
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
                            
                            # Для 422 ошибок делаем retry (если не последняя попытка)
                            if resp.status_code == 422 and attempt < max_retries:
                                error_body = resp.text[:200] if resp.text else ""
                                print(f"[RETRY] 422 error on attempt {attempt + 1}/{max_retries + 1}, retrying in {retry_delay}s: {error_body}")
                                gevent.sleep(retry_delay)
                                continue  # Повторяем запрос
                            
                            # Логируем тело ответа при ошибке для отладки
                            try:
                                error_body = resp.text[:1000]  # Первые 1000 символов
                                # Записываем в файл для надёжности
                                error_log_path = CSV_DIR / "error_responses.txt"
                                with error_log_path.open("a", encoding="utf-8") as ef:
                                    ef.write(f"\n[{datetime.now(timezone.utc).isoformat()}] Status {resp.status_code} for {path} (attempt {attempt + 1})\n")
                                    ef.write(f"Body: {error_body}\n")
                                    ef.write("-" * 80 + "\n")
                                # Также в stdout для быстрого просмотра
                                print(f"[ERROR] Response body (status {resp.status_code}): {error_body}")
                            except Exception as log_err:
                                print(f"[ERROR] Failed to log error response: {log_err}")
                            resp.failure(exception_text)
                        else:
                            resp.success()
                            
                            # Парсим JSON и сохраняем ключевые поля из ответа (только при успехе)
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
                            
                            # Успешный ответ - выходим из цикла retry
                            break
                except Exception as e:
                    # Если произошла ошибка при выполнении запроса (не HTTP ошибка), логируем и продолжаем
                    print(f"[ERROR] Exception during request attempt {attempt + 1}: {e}")
                    if attempt >= max_retries:
                        # Все попытки исчерпаны
                        break
                    gevent.sleep(retry_delay)

        finally:
            # Обновляем счётчики завершений и планируем остановку после достижения лимита завершённых попыток.
            global _attempts_completed, _quit_scheduled
            if TOTAL_REQUESTS_LIMIT > 0:
                should_schedule_quit = False
                with _requests_done_lock:
                    _attempts_completed += 1
                    _in_flight = max(0, _in_flight - 1)
                    _requests_done = _attempts_completed  # для обратной совместимости/логов
                    if _attempts_completed >= TOTAL_REQUESTS_LIMIT and not _quit_scheduled:
                        _quit_scheduled = True
                        should_schedule_quit = True

                if should_schedule_quit and self.environment and self.environment.runner:
                    print(f"[LOCUST] TOTAL_REQUESTS_LIMIT={TOTAL_REQUESTS_LIMIT} reached: completed={_attempts_completed}, in_flight={_in_flight}. runner.quit()")

                    def _do_quit(env):
                        try:
                            if env and env.runner:
                                env.runner.quit()
                        except Exception as e:
                            print(f"[LOCUST] runner.quit() failed: {e}")

                    gevent.spawn(_do_quit, self.environment)


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


@events.test_stop.add_listener
def _on_test_stop(environment, **kwargs):
    """Вызывается когда тест останавливается - даем время на завершение всех запросов"""
    global _requests_done
    if TOTAL_REQUESTS_LIMIT > 0:
        print(f"[LOCUST] Тест остановлен. Всего выполнено запросов: {_requests_done}")


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
    """
    Универсальное вытаскивание списка евентов из payload.
    """
    events_list: List[Dict[str, Any]] = []

    if isinstance(payload, dict):
        ev = payload.get("events")
        if isinstance(ev, list):
            events_list = [e for e in ev if isinstance(e, dict)]
        elif isinstance(ev, dict) and "items" in ev and isinstance(ev["items"], list):
            events_list = [e for e in ev["items"] if isinstance(e, dict)]
    elif isinstance(payload, list):
        events_list = [e for e in payload if isinstance(e, dict)]

    if DEBUG_COMPONENT_EVENTS:
        try:
            total = len(events_list)
            types = {}
            link_events_samples = []
            for e in events_list:
                t = e.get("event_type")
                types[t] = types.get(t, 0) + 1
                if t == "link_event" and len(link_events_samples) < 2:
                    # Сохраняем примеры link_event для анализа структуры
                    link_events_samples.append(e)
            print(f"[COMP_EVENTS_DEBUG] _extract_events: total={total}, by_type={types}")
            if link_events_samples:
                print(f"[COMP_EVENTS_DEBUG] link_event samples (first {len(link_events_samples)}):")
                for i, le in enumerate(link_events_samples):
                    print(f"[COMP_EVENTS_DEBUG]   link_event[{i}] keys: {list(le.keys())}")
                    print(f"[COMP_EVENTS_DEBUG]   link_event[{i}] sample: {le}")
        except Exception:
            pass

    return events_list


def _compute_component_rows(events: List[Dict[str, Any]]) -> List[Tuple[str, str, str, int, int, float]]:
    """
    Возвращает список (component_key, title, component_type, start_us, end_us, duration_ms)
    для component_event.
    """
    by_key: Dict[str, Dict[str, Any]] = {}
    total_events = len(events)
    component_events = 0
    for e in events:
        if e.get("event_type") != "component_event":
            continue
        component_events += 1
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

    if DEBUG_COMPONENT_EVENTS:
        try:
            print(
                f"[COMP_EVENTS_DEBUG] _compute_component_rows: "
                f"raw_events={total_events}, component_events={component_events}, rows={len(rows)}"
            )
        except Exception:
            pass

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
    if DEBUG_COMPONENT_EVENTS:
        print(f"[COMP_EVENTS_DEBUG] _fetch_events: url={url}, has_cookies={bool(cookies)}")
    resp = requests.get(url, cookies=cookies, verify=False, timeout=60)
    if DEBUG_COMPONENT_EVENTS:
        print(f"[COMP_EVENTS_DEBUG] _fetch_events: status={resp.status_code}")
    if not resp.ok:
        # Дадим максимум информации для диагностики (на тестовых стендах часто 401/403)
        err = RuntimeError(f"events fetch failed: status={resp.status_code}, url={url}, body={resp.text[:2000]}")
        setattr(err, "_events_status_code", resp.status_code)
        setattr(err, "_events_url", url)
        setattr(err, "_events_body", resp.text)
        raise err
    try:
        data = resp.json()
    except Exception as e:
        if DEBUG_COMPONENT_EVENTS:
            print(f"[COMP_EVENTS_DEBUG] _fetch_events: JSON decode error: {e}")
        raise
    return data


def _noop(*args, **kwargs):
    return None


# Вешаем методы на класс, чтобы можно было вызывать self._collect_component_timings
def _collect_component_timings(self: ApiUser, request_id: str, job_uuid: str) -> None:  # type: ignore[name-defined]
    """
    Получаем события по job_uuid и ждём, пока набор компонентных событий
    не "устаканится":
      - для первого job берём его количество компонент как эталон;
      - для остальных ждём, пока не наберём столько же component_event,
        либо пока не выйдем за максимальное время ожидания.
    """
    global _expected_components_per_job

    delay_sec = float(os.getenv("COMP_EVENTS_RETRY_DELAY", "1.0") or "1.0")
    max_wait_sec = float(os.getenv("COMP_EVENTS_MAX_WAIT_SEC", "90") or "90")
    max_attempts = max(1, int(max_wait_sec / delay_sec))

    attempts = 0
    rows: List[Tuple[str, str, str, int, int, float]] = []

    # Для первого job ждем стабилизации количества компонентов
    # (количество должно оставаться неизменным несколько попыток подряд)
    last_row_count = 0
    stable_count = 0
    required_stable_attempts = 3  # Количество попыток подряд с одинаковым количеством компонентов
    
    while attempts < max_attempts:
        attempts += 1
        payload = _fetch_events(self.host, job_uuid, cookies=getattr(self, "_auth_cookies", None))
        events = _extract_events(payload)
        
        # ВРЕМЕННОЕ ЛОГИРОВАНИЕ: проверяем все типы событий, включая link_event
        if DEBUG_COMPONENT_EVENTS and attempts == 1:
            event_types = {}
            link_events = []
            for e in events:
                et = e.get("event_type")
                event_types[et] = event_types.get(et, 0) + 1
                if et == "link_event":
                    link_events.append(e)
            print(f"[COMP_EVENTS_DEBUG] job_uuid={job_uuid} event_types={event_types}")
            if link_events:
                print(f"[COMP_EVENTS_DEBUG] Found {len(link_events)} link_events, sample: {link_events[0]}")
        
        rows = _compute_component_rows(events)
        row_count = len(rows)

        # Проверяем стабилизацию для первого job
        if _expected_components_per_job is None:
            if row_count == last_row_count and row_count > 0:
                stable_count += 1
            else:
                stable_count = 0
            last_row_count = row_count
            
            # Устанавливаем эталон только после стабилизации
            if stable_count >= required_stable_attempts and row_count > 0:
                _expected_components_per_job = row_count
                if DEBUG_COMPONENT_EVENTS:
                    print(f"[COMP_EVENTS_STABILIZE] job_uuid={job_uuid} set expected_components_per_job={_expected_components_per_job} after {attempts} attempts")
                break

        # Если эталон уже известен и мы его достигли (или превысили) — достаточно
        if _expected_components_per_job is not None and row_count >= _expected_components_per_job:
            break

        if attempts < max_attempts:
            if DEBUG_COMPONENT_EVENTS:
                print(
                    f"[COMP_EVENTS_RETRY] job_uuid={job_uuid} attempt={attempts} "
                    f"rows={row_count}, expected={_expected_components_per_job}, stable={stable_count}/{required_stable_attempts}, sleep {delay_sec}s"
                )
            time.sleep(delay_sec)

    if not rows:
        if DEBUG_COMPONENT_EVENTS:
            print(f"[COMP_EVENTS_RETRY] job_uuid={job_uuid} no component rows after {attempts} attempts")
        return

    if DEBUG_COMPONENT_EVENTS:
        print(
            f"[COMP_EVENTS_FINAL] job_uuid={job_uuid} rows={len(rows)}, "
            f"expected={_expected_components_per_job}, attempts={attempts}"
        )

    _write_component_rows(request_id, job_uuid, rows)


setattr(ApiUser, "_collect_component_timings", _collect_component_timings)

