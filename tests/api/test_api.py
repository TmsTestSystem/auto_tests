import os
from pathlib import Path
from dotenv import load_dotenv
import requests
from conftest import get_auth_cookies

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def test_api_projects_accessible():
    base_url = os.getenv("BASE_URL")
    assert base_url is not None, "BASE_URL not set"
    cookies = get_auth_cookies()
    # Проверяем доступ к списку проектов как к стабильно доступному эндпоинту
    resp = requests.get(f"{base_url.rstrip('/')}/api/projects", cookies=cookies)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}, body: {resp.text}"
    assert isinstance(resp.json(), list)