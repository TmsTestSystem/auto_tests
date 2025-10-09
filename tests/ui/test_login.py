import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from dotenv import load_dotenv
import os
from pathlib import Path
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

@pytest.mark.parametrize("email,password", [(os.getenv("LOGIN"), os.getenv("PASSWORD"))])
def test_login_success(email, password):
    assert email is not None, "LOGIN not set"
    assert password is not None, "PASSWORD not set"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_page = LoginPage(page)
        login_page.goto()
        login_page.login(email, password)
        assert login_page.is_create_project_button_visible(), "Кнопка 'Создать проект' не найдена после логина!"
        browser.close() 
