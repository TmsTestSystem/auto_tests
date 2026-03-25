import os
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv

# Отключаем предупреждения о незашифрованных запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

BASE_URL = os.getenv("BASE_URL", "http://192.168.0.10:3333").rstrip("/")
PROJECTS_API = f"{BASE_URL}/api/projects"
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")


def get_auth_cookies():
    resp = requests.post(
        f"{BASE_URL}/api/auth/sign_in",
        json={"email": LOGIN, "password": PASSWORD},
        verify=False,
    )
    resp.raise_for_status()
    return resp.cookies


def get_all_projects(cookies):
    resp = requests.get(PROJECTS_API, cookies=cookies, verify=False)
    resp.raise_for_status()
    return resp.json()


def delete_project(project_id, cookies):
    resp = requests.delete(f"{PROJECTS_API}/{project_id}", cookies=cookies, verify=False)
    resp.raise_for_status()
    return resp.status_code in (200, 204)


def clear_release_projects():
    cookies = get_auth_cookies()
    projects = get_all_projects(cookies)

    release_projects = [
        project
        for project in projects
        if (project.get("code") or "").startswith("release_e2e_")
    ]

    if not release_projects:
        print("[INFO] release_e2e проекты не найдены")
        return

    print(f"[INFO] Найдено {len(release_projects)} release_e2e проектов")

    deleted = 0
    for project in release_projects:
        project_id = project.get("id")
        code = project.get("code")
        if not project_id:
            print(f"[WARN] У проекта {code} нет ID, пропускаем")
            continue
        try:
            delete_project(project_id, cookies)
            deleted += 1
            print(f"[SUCCESS] Удалён проект {code}")
        except Exception as exc:
            print(f"[ERROR] Не удалось удалить {code}: {exc}")

    print(f"[INFO] Удалено {deleted} из {len(release_projects)} проектов")


if __name__ == "__main__":
    clear_release_projects()

