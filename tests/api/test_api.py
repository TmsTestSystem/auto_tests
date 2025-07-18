import requests
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def get_token_cookie():
    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    assert email is not None, "LOGIN not set"
    assert password is not None, "PASSWORD not set"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        login_page = LoginPage(page)
        login_page.goto()
        login_page.login(email, password)
        cookies = page.context.cookies()
        token_cookie = next((c for c in cookies if c['name'] == 'swnkc'), None)
        browser.close()
        return token_cookie

def test_api_with_token():
    base_url = os.getenv("BASE_URL")
    assert base_url is not None, "BASE_URL not set"
    token_cookie = get_token_cookie()
    assert token_cookie is not None, "swnkc cookie not found!"
    cookies = {token_cookie['name']: token_cookie['value']}
    # Пример запроса к защищенному API
    response = requests.get(f"{base_url}/api/protected-endpoint", cookies=cookies)
    assert response.status_code == 200 