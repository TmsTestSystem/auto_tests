from playwright.sync_api import Page
from .base_page import BasePage
import os

class LoginPage(BasePage):
    EMAIL_INPUT = 'input[name="email"]'
    PASSWORD_INPUT = 'input[name="password"]'
    SUBMIT_BUTTON = 'button[type="submit"]'

    def __init__(self, page: Page):
        super().__init__(page)
        self.login_url = f"{os.getenv('BASE_URL')}/login"

    def goto(self):
        self.page.goto(self.login_url)

    def login(self, email: str, password: str):
        self.page.fill(self.EMAIL_INPUT, email)
        self.page.fill(self.PASSWORD_INPUT, password)
        self.page.click(self.SUBMIT_BUTTON)
        self.page.wait_for_load_state('networkidle')

    def is_create_project_button_visible(self, timeout=15000):
        selector = 'button:has-text("Создать проект")'
        self.page.wait_for_selector(selector, timeout=timeout)
        return self.page.is_visible(selector) 