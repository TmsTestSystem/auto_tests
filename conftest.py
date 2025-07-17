import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
import os
import time

def save_screenshot(page, test_name):
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    screenshot_base = test_name
    screenshot_path = os.path.join(screenshots_dir, f"{screenshot_base}.png")
    # Если файл уже есть, добавляем timestamp
    if os.path.exists(screenshot_path):
        screenshot_path = os.path.join(screenshots_dir, f"{screenshot_base}_{int(time.time())}.png")
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"[SCREENSHOT] Скриншот сохранён: {screenshot_path}")

@pytest.fixture(scope="function")
def login_page():
    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    assert email is not None, "LOGIN not set"
    assert password is not None, "PASSWORD not set"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_page = LoginPage(page)
        login_page.goto()
        login_page.login(email, password)
        yield page
        browser.close() 