from playwright.sync_api import Page
from .base_page import BasePage
import os
import time

class ProjectPage(BasePage):
    CREATE_BUTTON = 'button:has-text("Создать проект")'
    MODAL_FORM = 'form'
    MODAL_BACKDROP = '.Modal__Backdrop'  # примерный селектор backdrop
    PROJECT_LIST = '[data-testid="project-list"]'  # заменить на актуальный селектор списка проектов
    PROJECT_ROW = 'a[href^="/projects/"]'  # ссылка на проект
    SUBMIT_BUTTON = 'button[aria-label="Отправить"]'

    def __init__(self, page: Page):
        super().__init__(page)
        self.projects_url = f"{os.getenv('BASE_URL')}/projects"

    def goto(self):
        self.page.goto(self.projects_url)
        self.page.wait_for_load_state('networkidle')

    def open_create_project_modal(self):
        self.page.wait_for_selector(self.CREATE_BUTTON, timeout=15000)
        self.page.click(self.CREATE_BUTTON)
        self.page.wait_for_selector(self.MODAL_FORM, timeout=10000)

    def create_project(self, title: str, code: str, git: str, default_branch: str):
        for label, value in [
            ('title', title),
            ('code', code),
            ('git', git),
            ('default_branch', default_branch),
        ]:
            self.page.wait_for_selector(f"input[aria-label='{label}']", timeout=10000)
            self.page.fill(f"input[aria-label='{label}']", value)
        self.page.click(self.SUBMIT_BUTTON)

    def wait_modal_close(self):
        # Ждём исчезновения формы или backdrop
        self.page.wait_for_selector(self.MODAL_FORM, state='detached', timeout=15000)
        # self.page.wait_for_selector(self.MODAL_BACKDROP, state='detached', timeout=15000)  # если есть backdrop

    def find_project_in_list(self, title: str):
        self.page.wait_for_selector('div[aria-label="projects_card"]', timeout=10000)
        cards = self.page.query_selector_all('div[aria-label="projects_card"]')
        for card in cards:
            title_div = card.query_selector('div[aria-label="projects_card_title"]')
            if title_div and title_div.inner_text().strip() == title:
                link = card.query_selector('a[aria-label="projects_card_link"]')
                return link
        return None

    def goto_project(self, code: str):
        prj = self.find_project_in_list(code)
        if prj:
            prj.click()
            self.page.wait_for_load_state('networkidle')
            return True
        return False

    def check_required_buttons(self, required_aria_labels):
        for label in required_aria_labels:
            assert self.page.is_visible(f'button[aria-label="{label}"]'), f'Кнопка с aria-label="{label}" не найдена!' 

    # Удалены методы:
    # - open_file_panel
    # - open_create_file_menu
    # - get_file_type_buttons
    # - create_file_of_type 