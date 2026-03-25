"""
Скрипт для запуска нагрузочного тестирования компонентов.
Для каждого прогона создаёт ОТДЕЛЬНЫЙ проект с уникальным кодом
и импортирует в него `project_for_component_test.zip`.
"""

import argparse
import datetime as dt
import os
import pathlib
import subprocess
import sys
import time
from typing import Tuple, Optional

import requests
import urllib3
import json

BASE_DIR = pathlib.Path(__file__).parent.resolve()
PROJ_DIR = BASE_DIR.parent.resolve()
PROJECT_ROOT = PROJ_DIR.parent.resolve()
DEFAULT_COMPARE = PROJ_DIR / "compare_jobs_vs_events.py"

# Подключаем утилиты авторизации/BASE_URL из проекта
sys.path.insert(0, str(PROJECT_ROOT))
from utils.auth_utils import get_auth_cookies, get_api_base_url  # type: ignore  # noqa: E402

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Маппинг хостов на URL (как в conftest.py)
HOST_URLS = {
    "st1": "https://decision-flow-frontend-st1.df-st.b-pl.cloud2",
    "st2": "https://decision-flow-frontend-st2.df-st.b-pl.cloud2",
    "st3": "https://decision-flow-frontend-st3.df-st.b-pl.cloud2",
    "st4": "https://decision-flow-frontend-web-1.df-st4.cloud2.b-pl.pro",
    "local-a": "http://192.168.0.10:3333",
    "local-b": "http://localhost:3334",
    "local-c": "http://localhost:3335",
    "local-192": "http://192.168.0.10:3333",
    "local-192-https": "https://192.168.0.10/"
}


def resolve_host(host: str) -> str:
    """
    Преобразует алиас хоста в полный URL.
    Если передан полный URL (начинается с http:// или https://), возвращает его как есть.
    Если передан алиас (st1, st2, local-192 и т.д.), возвращает соответствующий URL.
    """
    if host.startswith(("http://", "https://")):
        return host.rstrip("/")
    
    if host in HOST_URLS:
        return HOST_URLS[host].rstrip("/")
    
    # Если алиас не найден, возвращаем как есть (может быть пользователь указал что-то своё)
    print(f"[WARNING] Неизвестный алиас хоста '{host}'. Используем как есть.")
    print(f"[INFO] Доступные алиасы: {', '.join(HOST_URLS.keys())}")
    return host.rstrip("/")


def find_compare_script() -> pathlib.Path:
    candidates = [
        DEFAULT_COMPARE,
        BASE_DIR / "compare_jobs_vs_events.py",
        PROJ_DIR / "compare_jobs_vs_events.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Резервный вариант: рекурсивный поиск до корня проекта
    for p in PROJ_DIR.rglob("compare_jobs_vs_events.py"):
        return p
    raise FileNotFoundError("compare_jobs_vs_events.py не найден в проекте. Разместите его в корне проекта.")


def setup_component_project() -> Tuple[str, Optional[dict]]:
    """
    Создать ОТДЕЛЬНЫЙ проект для компонентного нагрузочного теста
    и импортировать в него zip `project_for_component_test.zip`.

    Код проекта всегда уникален (component_load_YYYYMMDDHHMMSS), чтобы
    каждый прогон был изолирован и легко отличим в UI.

    Возвращает (project_code, project_info) — при ошибке импорта project_info может быть None.
    """
    base_url = get_api_base_url()
    cookies = get_auth_cookies()

    ts = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    project_code = f"component_load_{ts}"
    project_title = f"Component Load Project {ts}"

    print(f"[COMPONENT_LOAD_SETUP] Создаём проект: {project_code}")
    create_data = {
        "title": project_title,
        "code": project_code,
        "description": f"API тестовый проект для нагрузочного тестирования компонентов {project_code}",
        "gradient": "#9D80CB,#F7C2E6",
        "type": "directory",
    }
    files = {
        "project_json": (None, json.dumps(create_data), "application/json"),
        "zip_template": ("empty.zip", b"", "application/octet-stream"),
    }
    resp = requests.post(
        f"{base_url}/api/projects",
        cookies=cookies,
        files=files,
        verify=False,
        timeout=60,
    )
    resp.raise_for_status()
    project_info = resp.json()

    # Небольшая пауза, чтобы проект успел полностью инициализироваться до импорта репозитория
    print("[COMPONENT_LOAD_SETUP] Ждём 2 секунды после создания проекта...")
    time.sleep(2)

    # Импортируем zip project_for_component_test.zip из корня репозитория
    zip_path = PROJECT_ROOT / "project_for_component_test.zip"
    if not zip_path.exists():
        print(f"[COMPONENT_LOAD_WARN] ZIP файл не найден: {zip_path}")
        return project_code, project_info

    upload_url = f"{base_url}/api/ide/{project_code}/branch/master/git/repository/upload"
    print(f"[COMPONENT_LOAD_SETUP] Импортируем ZIP: {zip_path} -> {upload_url}")
    with zip_path.open("rb") as f:
        data = f.read()

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/binary",
    }
    upload_resp = requests.post(
        upload_url,
        data=data,
        headers=headers,
        cookies=cookies,
        verify=False,
        timeout=180,
    )
    print(f"[COMPONENT_LOAD_SETUP] ZIP upload status: {upload_resp.status_code}")
    if not upload_resp.ok:
        # Печатаем тело ответа для отладки (обрезаем до 1000 символов)
        print("[COMPONENT_LOAD_SETUP] ZIP upload response body:", upload_resp.text[:1000])
        upload_resp.raise_for_status()
    print(f"[COMPONENT_LOAD_SETUP] ZIP импортирован, статус: {upload_resp.status_code}")

    # Небольшая пауза, чтобы репозиторий успел примениться и процессы проиндексировались
    wait_after_import_sec = float(os.getenv("PROJECT_IMPORT_WAIT_SEC", "20") or "20")
    print(f"[COMPONENT_LOAD_SETUP] Ждём {wait_after_import_sec} секунд после импорта для индексации процессов...")
    time.sleep(wait_after_import_sec)

    # Проверяем готовность проекта: делаем тестовый запрос к процессу
    process_path = os.getenv("LOAD_PROCESS_PATH", "Test_1.df.json")
    test_url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={process_path}"
    test_payload = {
        "request_meta": {
            "object_id": "test_readiness_check",
            "request_id": "test_readiness_check",
            "tags": "test",
        },
        "request_data": {
            "amount_requested": {"currency_code": "RUB", "value": 12},
            "auto": {"VIN": "test", "is_new": True, "is_used": True, "owner": {"firstname": "test", "lastname": "test", "middlename": "test", "passport": {"number": "test", "series": "test"}}},
            "co_issuers": [],
            "initial_payment": {"currency_code": "RUB", "value": 31},
            "issuer": {"firstname": "test", "lastname": "test", "middlename": "test", "passport": {"number": "test", "series": "test"}},
        },
    }
    
    max_readiness_checks = 5
    readiness_check_delay = 3.0
    project_ready = False
    
    for check_num in range(1, max_readiness_checks + 1):
        try:
            print(f"[COMPONENT_LOAD_SETUP] Проверка готовности проекта (попытка {check_num}/{max_readiness_checks})...")
            test_resp = requests.post(
                test_url,
                json=test_payload,
                cookies=cookies,
                verify=False,
                timeout=30,
            )
            if test_resp.status_code == 200:
                print(f"[COMPONENT_LOAD_SETUP] Проект готов! Тестовый запрос вернул 200")
                project_ready = True
                break
            elif test_resp.status_code == 422:
                error_msg = test_resp.text[:200] if test_resp.text else ""
                print(f"[COMPONENT_LOAD_SETUP] Проект ещё не готов (422): {error_msg}")
            else:
                print(f"[COMPONENT_LOAD_SETUP] Неожиданный статус при проверке готовности: {test_resp.status_code}")
        except Exception as e:
            print(f"[COMPONENT_LOAD_SETUP] Ошибка при проверке готовности: {e}")
        
        if check_num < max_readiness_checks:
            time.sleep(readiness_check_delay)
    
    if not project_ready:
        print(f"[COMPONENT_LOAD_SETUP_WARN] Проект не прошёл проверку готовности после {max_readiness_checks} попыток. Продолжаем запуск, но возможны ошибки 422.")
    else:
        print(f"[COMPONENT_LOAD_SETUP] Проект готов к нагрузочному тестированию")

    return project_code, project_info


def delete_project_safely(project_code: str, project_info: Optional[dict]) -> None:
    """Удалить проект после прогона нагрузочного теста (best-effort)."""
    if not project_info or "id" not in project_info:
        return
    base_url = get_api_base_url()
    cookies = get_auth_cookies()
    try:
        resp = requests.delete(
            f"{base_url}/api/projects/{project_info['id']}",
            cookies=cookies,
            verify=False,
            timeout=60,
        )
        print(f"[COMPONENT_LOAD_CLEANUP] DELETE /api/projects/{project_info['id']} -> {resp.status_code}")
    except Exception as e:
        print(f"[COMPONENT_LOAD_CLEANUP_WARN] Ошибка при удалении проекта {project_code}: {e}")


def run(users: int, spawn_rate: int, duration_sec: int, host: str, num_requests: int = None) -> None:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = BASE_DIR / "reports" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    # Преобразуем алиас хоста в полный URL (если нужно)
    resolved_host = resolve_host(host)
    
    # Устанавливаем BASE_URL из переданного хоста для API вызовов
    os.environ["BASE_URL"] = resolved_host
    print(f"[COMPONENT_LOAD] Используем BASE_URL: {os.environ['BASE_URL']}")

    # 0) Создаём или используем проект TEST12 и импортируем project_for_component_test.zip
    project_code, project_info = setup_component_project()

    # 1) Запускаем Locust с HTML отчётом
    cmd = [
        "locust",
        "-f",
        str(PROJ_DIR / "locustfile.py"),  # Используем locustfile.py из load_testing
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "--host",
        resolved_host,
        "--only-summary",
        "--stop-timeout",
        "120",
        "--html",
        str(out_dir / "locust_report.html"),
    ]
    # Добавляем либо количество запросов (рассчитываем время), либо время
    if num_requests:
        # Останавливаем тест по количеству запросов (TOTAL_REQUESTS), а не по времени.
        # Время ставим заведомо большим; quit() сделает остановку сразу после достижения лимита.
        cmd.extend(["-t", "86400s"])
        print(f"[COMPONENT_LOAD] Запуск на {num_requests} запросов (остановка по TOTAL_REQUESTS, таймер=86400s)")
    else:
        cmd.extend(["-t", f"{duration_sec}s"])
    env_locust = os.environ.copy()
    # Прокидываем код проекта и путь процесса для locustfile.py через переменные окружения
    env_locust["LOAD_PROJECT_CODE"] = project_code
    env_locust["LOAD_BRANCH"] = "master"
    # Путь процесса внутри импортированного проекта (Test_1.df.json для компонентного тестирования)
    env_locust["LOAD_PROCESS_PATH"] = os.getenv("LOAD_PROCESS_PATH", "Test_1.df.json")
    # Передаём REPORT_DIR в Locust, чтобы jobs_from_responses.csv сохранялся в правильное место
    env_locust["REPORT_DIR"] = str(out_dir)
    # Включаем сбор метрик по компонентам через /api/events/{job_uuid}
    env_locust["COLLECT_COMPONENT_EVENTS"] = os.getenv("COLLECT_COMPONENT_EVENTS", "true")
    if num_requests:
        env_locust["TOTAL_REQUESTS"] = str(num_requests)

    # Не падаем на ошибках Locust (exit code 1 при наличии failed requests - это нормально)
    print(f"[COMPONENT_LOAD] Запускаем Locust с параметрами: users={users}, spawn_rate={spawn_rate}, num_requests={num_requests}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env_locust, check=False)
    print(f"[COMPONENT_LOAD] Locust завершился с кодом: {result.returncode}")

    # CSV файлы (requests.csv, requests_events.csv) теперь создаются напрямую в REPORT_DIR через locustfile.py
    # Копирование больше не требуется

    # 2) Генерируем отчёт сравнения в ту же папку
    compare_script = find_compare_script()
    env = os.environ.copy()
    env["BASE_DIR"] = str(BASE_DIR)
    env["REPORT_DIR"] = str(out_dir)
    # Убрали фильтры по умолчанию, чтобы показывать ВСЕ данные в графике и таблице
    # Если нужно ограничить, можно добавить --limit, --bucket-ms и т.д. через переменные окружения
    default_args = []
    # compare_jobs_vs_events.py не должен ломать весь прогон (особенно если Locust завершился с code=1)
    subprocess.run([sys.executable, str(compare_script), *default_args], cwd=str(BASE_DIR), env=env, check=False)

    # 3) Небольшая пауза перед сборкой компонентных отчётов,
    # чтобы на "тяжёлых" стендах все events по компонентам успели записаться/проиндексироваться.
    delay_before_components_sec = float(os.getenv("COMPONENT_AGGREGATION_DELAY_SEC", "60") or "60")
    print(f"[COMPONENT_LOAD] Ждём {delay_before_components_sec} секунд перед сборкой отчётов по компонентам...")
    time.sleep(delay_before_components_sec)

    # Затем генерируем файлы и отчёты по компонентам
    build_timings_script = BASE_DIR / "scripts" / "build_component_timings.py"
    build_diagram_and_gaps_script = BASE_DIR / "scripts" / "build_diagram_and_gaps.py"
    component_report_script = BASE_DIR / "scripts" / "generate_component_report.py"
    aggregated_report_script = BASE_DIR / "scripts" / "generate_aggregated_report.py"
    grouped_report_script = BASE_DIR / "scripts" / "generate_grouped_report.py"
    link_events_script = BASE_DIR / "scripts" / "build_link_events.py"
    link_report_script = BASE_DIR / "scripts" / "generate_link_report.py"
    diagram_report_script = BASE_DIR / "scripts" / "generate_diagram_report.py"
    gaps_report_script = BASE_DIR / "scripts" / "generate_gaps_report.py"
    level_comparison_script = BASE_DIR / "scripts" / "generate_level_comparison_report.py"
    execution_summary_script = BASE_DIR / "scripts" / "generate_execution_summary_report.py"
    
    # Сначала строим CSV файлы по компонентам
    if build_timings_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(build_timings_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать файлы по компонентам: {e}")
    else:
        print(f"[INFO] Скрипт build_component_timings.py не найден, пропускаем генерацию CSV")

    # link_event: собираем отдельный CSV из /api/events/{job_uuid} и строим HTML отчёт
    if link_events_script.exists():
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(link_events_script),
                    "--report-dir",
                    str(out_dir),
                    "--project-code",
                    str(project_code),
                    "--branch",
                    "master",
                ],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось собрать link_event CSV: {e}")
    else:
        print(f"[INFO] Скрипт build_link_events.py не найден, пропускаем link_event CSV")

    if link_report_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(link_report_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать link_event HTML отчёт: {e}")
    else:
        print(f"[INFO] Скрипт generate_link_report.py не найден, пропускаем link_event HTML")

    # Затем строим диаграмму и GAP отчёты (на основе component_timings.csv)
    if build_diagram_and_gaps_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(build_diagram_and_gaps_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать diagram/gaps CSV: {e}")
    
    # Затем создаём детальный отчёт
    if component_report_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(component_report_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать детальный отчёт по компонентам: {e}")
    
    # Затем создаём агрегированный отчёт
    if aggregated_report_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(aggregated_report_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать агрегированный отчёт по компонентам: {e}")
    
    # Затем создаём групповой отчёт
    if grouped_report_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(grouped_report_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать групповой отчёт по компонентам: {e}")

    # Отчёт по диаграмме (рост времени диаграммы по прогонам)
    if diagram_report_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(diagram_report_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать отчёт по диаграмме: {e}")

    # Отчёт по GAP между компонентами
    if gaps_report_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(gaps_report_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать отчёт по GAP: {e}")

    # Отчёт сравнения производительности по уровням (test1/test2/test3)
    if level_comparison_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(level_comparison_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать отчёт сравнения по уровням: {e}")

    # Отчёт сводки выполнения: стрелки vs компоненты по каждому прогону
    if execution_summary_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(execution_summary_script), "--report-dir", str(out_dir)],
                cwd=str(BASE_DIR),
                check=False,
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать отчёт сводки выполнения: {e}")

    # Удаляем проект после сбора всех результатов
    # Проверяем флаг KEEP_LOAD_PROJECT: если он установлен в 'true', проект не удаляем
    keep_project = os.getenv("KEEP_LOAD_PROJECT", "").lower() == "true"
    if keep_project:
        print(f"[COMPONENT_LOAD_CLEANUP] Проект {project_code} сохранён (KEEP_LOAD_PROJECT=true)")
    else:
        print(f"[COMPONENT_LOAD_CLEANUP] Удаляем проект {project_code} после сбора результатов...")
        delete_project_safely(project_code, project_info)

    print(f"Done. Reports: {out_dir}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Запускает нагрузочный тест компонентов Locust и генерирует отчёт сравнения")
    p.add_argument("--users", "-u", type=int, default=100, help="Concurrent users")
    p.add_argument("--spawn-rate", "-r", type=int, default=50, help="Spawn rate")
    p.add_argument("--duration", "-t", type=int, default=None, help="Duration in seconds")
    p.add_argument("--num-requests", "-n", type=int, default=None, help="Total number of requests")
    p.add_argument(
        "--host", "-H", 
        type=str, 
        default="local-192", 
        help="Целевой хост (URL или алиас: st1, st2, st3, st4, local-a, local-b, local-c, local-192)"
    )
    args = p.parse_args(argv)
    if args.duration is None and args.num_requests is None:
        args.duration = 60  # По умолчанию 60 секунд
    run(args.users, args.spawn_rate, args.duration, args.host, args.num_requests)


if __name__ == "__main__":
    main()
