"""
Подготовка проекта для компонентного нагрузочного теста.

Шаги:
1) Создать проект TEST12 (если уже существует — переиспользовать)
2) Импортировать zip `project_for_component_test.zip` в ветку master
3) Подождать 5 секунд, пока импорт применится
4) Запустить процесс: /api/ide/TEST12/branch/master/bps/call?path=Test_1.df.json

Требования:
- В .env должны быть BASE_URL, LOGIN, PASSWORD (используем utils.auth_utils)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import urllib3
import json

# Обеспечиваем импорт модулей из корня репозитория при запуске файла как скрипта
REPO_ROOT = Path(__file__).resolve().parents[3]  # .../auto-test2_0
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.auth_utils import get_api_base_url, get_auth_cookies  # noqa: E402


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_CODE = "TEST12"
BRANCH = "master"
ZIP_NAME = "project_for_component_test.zip"
PROCESS_PATH = "Test_1.df.json"


def _get_project_by_code(projects: list[dict], code: str) -> Optional[dict]:
    for p in projects:
        if p.get("code") == code:
            return p
    return None


def ensure_project_exists(project_code: str) -> dict:
    base_url = get_api_base_url()
    cookies = get_auth_cookies()

    # 1) пробуем найти проект
    resp = requests.get(
        f"{base_url}/api/projects",
        cookies=cookies,
        verify=False,
        timeout=60,
    )
    resp.raise_for_status()
    existing = _get_project_by_code(resp.json(), project_code)
    if existing:
        print(f"[SETUP] Проект уже существует: {project_code} (id={existing.get('id')})")
        return existing

    # 2) создаём
    create_data = {
        "title": f"Component Load Project {project_code}",
        "code": project_code,
        "description": f"API тестовый проект {project_code}",
        "gradient": "#9D80CB,#F7C2E6",
        "type": "directory",
    }
    print(f"[SETUP] Создаём проект: {project_code}")
    files = {
        "project_json": (None, json.dumps(create_data), "application/json"),
        "zip_template": ("empty.zip", b"", "application/octet-stream"),
    }
    create_resp = requests.post(
        f"{base_url}/api/projects",
        cookies=cookies,
        files=files,
        verify=False,
        timeout=60,
    )
    # Если кто-то параллельно создал — перечитаем список и продолжим
    if create_resp.status_code in (409, 422):
        print(f"[SETUP] Проект, похоже, уже создан параллельно (status={create_resp.status_code}). Переиспользуем.")
        resp2 = requests.get(f"{base_url}/api/projects", cookies=cookies, verify=False, timeout=60)
        resp2.raise_for_status()
        existing2 = _get_project_by_code(resp2.json(), project_code)
        if existing2:
            return existing2
    create_resp.raise_for_status()
    return create_resp.json()


def import_zip_to_project(project_code: str, zip_path: Path) -> None:
    base_url = get_api_base_url()
    cookies = get_auth_cookies()

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP файл не найден: {zip_path}")

    upload_url = f"{base_url}/api/ide/{project_code}/branch/{BRANCH}/git/repository/upload"
    print(f"[SETUP] Импортируем ZIP: {zip_path} -> {upload_url}")

    data = zip_path.read_bytes()
    headers = {"Accept": "*/*", "Content-Type": "application/binary"}
    upload_resp = requests.post(
        upload_url,
        data=data,
        headers=headers,
        cookies=cookies,
        verify=False,
        timeout=180,
    )
    print(f"[SETUP] ZIP upload status: {upload_resp.status_code}")
    if not upload_resp.ok:
        print("[SETUP] ZIP upload response body:", upload_resp.text[:1000])
        upload_resp.raise_for_status()


def call_process(project_code: str, process_path: str) -> Dict[str, Any]:
    base_url = get_api_base_url()
    cookies = get_auth_cookies()

    url = f"{base_url}/api/ide/{project_code}/branch/{BRANCH}/bps/call"
    params = {"path": process_path}

    payload = {
        "request_meta": {
            "object_id": "component_load_setup",
            "request_id": f"component_load_setup_{int(time.time())}",
            "tags": "component_load_setup",
        },
        "request_data": {},  # на старте оставляем пустым; при необходимости расширим
    }

    print(f"[SETUP] Запуск процесса: {url}?path={process_path}")
    resp = requests.post(
        url,
        params=params,
        json=payload,
        cookies=cookies,
        verify=False,
        timeout=180,
    )
    print(f"[SETUP] bps/call status: {resp.status_code}")
    if not resp.ok:
        print("[SETUP] bps/call response body:", resp.text[:2000])
        resp.raise_for_status()
    return resp.json()


def main() -> None:
    zip_path = REPO_ROOT / ZIP_NAME

    ensure_project_exists(PROJECT_CODE)
    import_zip_to_project(PROJECT_CODE, zip_path)

    print("[SETUP] Ждём 5 секунд после импорта проекта...")
    time.sleep(5)

    result = call_process(PROJECT_CODE, PROCESS_PATH)
    print("[SETUP] Done. Response (truncated):")
    print(str(result)[:2000])


if __name__ == "__main__":
    main()

