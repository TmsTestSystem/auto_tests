import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import urllib3

# Загружаем переменные окружения из .env файла,
# но НЕ перетираем уже установленные переменные (особенно BASE_URL,
# которую мы пробрасываем из run_component_load.py / run.py под конкретный стенд).
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)

# Отключаем предупреждения о небезопасных запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def normalize_base_url(base_url):
    """Нормализовать локальный URL под secure auth cookie."""
    base_url = (base_url or "https://192.168.0.10/").strip().rstrip("/")
    if base_url == "http://192.168.0.10:3333":
        return "https://192.168.0.10"
    return base_url

def get_api_base_url():
    """Получить BASE_URL из переменных окружения"""
    return normalize_base_url(os.getenv("BASE_URL", "https://192.168.0.10/"))

def get_auth_cookies():
    """
    Получить куки авторизации через API логин
    """
    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    api_base_url = get_api_base_url()
    resp = requests.post(f"{api_base_url}/api/auth/sign_in", json={"email": email, "password": password}, verify=False)
    resp.raise_for_status()
    return resp.cookies
