import argparse
import datetime as dt
import os
import pathlib
import subprocess
import sys
from typing import Tuple, Optional

import requests
import urllib3

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
    "st4": "https://decision-flow-web-1.df-st4.cloud2.b-pl.pro",
    "local-a": "http://localhost:3333",
    "local-b": "http://localhost:3334",
    "local-c": "http://localhost:3335",
    "local-192": "http://192.168.0.7:3333"
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


def create_and_import_load_project() -> Tuple[str, Optional[dict]]:
    """
    Создать проект для нагрузочного теста и импортировать в него zip test_load-branch-main.zip.

    Возвращает (project_code, project_info) — при ошибке импорта project_info может быть None.
    """
    base_url = get_api_base_url()
    cookies = get_auth_cookies()

    # Уникальный код проекта, чтобы не конфликтовать с существующими
    ts = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    project_code = f"test_load_{ts}"
    project_title = f"Test Load Project {ts}"

    # Формат полностью повторяет рабочий тест test_proj_func из tests/api/test_api.py
    create_data = {
        "title": project_title,
        "code": project_code,
        "git_url": "/opt/app/empty_repo",
        "default_branch": "master",
        "gradient": "blue",
        "description": f"API тестовый проект {project_code}",
        "git": "/opt/app/empty_repo",
    }

    print(f"[LOAD_SETUP] Создаём проект: {project_code}")
    resp = requests.post(
        f"{base_url}/api/projects",
        json=create_data,
        cookies=cookies,
        verify=False,
        timeout=60,
    )
    resp.raise_for_status()
    project_info = resp.json()

    # Небольшая пауза, чтобы проект успел полностью инициализироваться до импорта репозитория
    import time as _time

    print("[LOAD_SETUP] Ждём 2 секунды после создания проекта...")
    _time.sleep(2)

    # Импортируем zip test_load-branch-main.zip из корня репозитория
    zip_path = PROJECT_ROOT / "test_load-branch-main.zip"
    if not zip_path.exists():
        print(f"[LOAD_WARN] ZIP файл не найден: {zip_path}")
        return project_code, project_info

    upload_url = f"{base_url}/api/ide/{project_code}/branch/master/git/repository/upload"
    print(f"[LOAD_SETUP] Импортируем ZIP: {zip_path} -> {upload_url}")
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
    print(f"[LOAD_SETUP] ZIP upload status: {upload_resp.status_code}")
    if not upload_resp.ok:
        # Печатаем тело ответа для отладки (обрезаем до 1000 символов)
        print("[LOAD_SETUP] ZIP upload response body:", upload_resp.text[:1000])
        upload_resp.raise_for_status()
    print(f"[LOAD_SETUP] ZIP импортирован, статус: {upload_resp.status_code}")

    # Небольшая пауза, чтобы репозиторий успел примениться и процессы проиндексировались
    print("[LOAD_SETUP] Ждём 10 секунд после импорта для индексации процессов...")
    _time.sleep(10)

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
        print(f"[LOAD_CLEANUP] DELETE /api/projects/{project_info['id']} -> {resp.status_code}")
    except Exception as e:
        print(f"[LOAD_CLEANUP_WARN] Ошибка при удалении проекта {project_code}: {e}")


def run(users: int, spawn_rate: int, duration_sec: int, host: str, num_requests: int = None) -> None:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = BASE_DIR / "reports" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    # Преобразуем алиас хоста в полный URL (если нужно)
    resolved_host = resolve_host(host)
    
    # Устанавливаем BASE_URL из переданного хоста для API вызовов
    os.environ["BASE_URL"] = resolved_host
    print(f"[LOAD] Используем BASE_URL: {os.environ['BASE_URL']}")

    # 0) Создаём и импортируем проект под нагрузку
    project_code, project_info = create_and_import_load_project()

    # 1) Запускаем Locust с HTML отчётом
    cmd = [
        "locust",
        "-f",
        str(PROJ_DIR / "locustfile.py"),  # Используем locustfile.py из load_testing, а не из load/
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "--host",
        resolved_host,
        "--only-summary",
        "--html",
        str(out_dir / "locust_report.html"),
    ]
    # Добавляем либо количество запросов (рассчитываем время), либо время
    if num_requests:
        # Рассчитываем примерное время: при spawn_rate запросов в секунду
        estimated_duration = max(60, int(num_requests / spawn_rate) + 30)  # Минимум 60 сек, плюс запас
        cmd.extend(["-t", f"{estimated_duration}s"])
        print(f"[LOAD] Запуск на {num_requests} запросов (примерно {estimated_duration} секунд при {spawn_rate} req/s)")
    else:
        cmd.extend(["-t", f"{duration_sec}s"])
    env_locust = os.environ.copy()
    # Прокидываем код проекта и путь процесса для locustfile.py через переменные окружения
    env_locust["LOAD_PROJECT_CODE"] = project_code
    env_locust["LOAD_BRANCH"] = "master"
    # Путь процесса внутри импортированного проекта (по умолчанию грузим ComplexCheck)
    env_locust["LOAD_PROCESS_PATH"] = os.getenv("LOAD_PROCESS_PATH", "Flows/Loan/ComplexCheck.df.json")
    # Передаём REPORT_DIR в Locust, чтобы jobs_from_responses.csv сохранялся в правильное место
    env_locust["REPORT_DIR"] = str(out_dir)

    try:
        # Не падаем на ошибках Locust (exit code 1 при наличии failed requests - это нормально)
        subprocess.run(cmd, cwd=str(BASE_DIR), env=env_locust, check=False)
    finally:
        # По умолчанию удаляем проект после прогона,
        # но можно сохранить его для анализа из UI, установив KEEP_LOAD_PROJECT=true
        keep_project = os.getenv("KEEP_LOAD_PROJECT", "false").lower() in ("1", "true", "yes")
        if keep_project:
            print(f"[LOAD_CLEANUP] KEEP_LOAD_PROJECT включён — проект {project_code} НЕ будет удалён")
        else:
            delete_project_safely(project_code, project_info)

    # CSV файлы (requests.csv, requests_events.csv) теперь создаются напрямую в REPORT_DIR через locustfile.py
    # Копирование больше не требуется

    # 2) Генерируем отчёт сравнения в ту же папку
    compare_script = find_compare_script()
    env = os.environ.copy()
    env["BASE_DIR"] = str(BASE_DIR)
    env["REPORT_DIR"] = str(out_dir)
    # Скрытые фильтры по умолчанию для компактного отчёта; настраиваются здесь без CLI флагов
    default_args = [
        "--bucket-ms", "20",
        "--samples-per-bucket", "3",
        "--limit", "500",
        # Пример: оставляем обе колонки дельт по умолчанию; аргумент columns опционален
        # "--columns", "request_id,delta_started_at_vs_object_id_ms,delta_finished_at_vs_response_end_ms,started_at,object_id,finished_at,response_end,job_duration",
    ]
    subprocess.run([sys.executable, str(compare_script), *default_args], cwd=str(BASE_DIR), env=env, check=True)

    print(f"Done. Reports: {out_dir}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Запускает нагрузочный тест Locust и генерирует отчёт сравнения")
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
