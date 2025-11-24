from playwright.sync_api import Page
from .base_page import BasePage
import time


class CommitPage(BasePage):
    """Page Object для работы с коммитами"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    def open_commit_panel(self):
        """Открывает панель коммитов"""
        self.page.get_by_role("button", name="board_toolbar_commit_button").click()
        time.sleep(2)

    def stage_all_files(self):
        """Ставит все файлы в stage"""
        self.page.get_by_role("treeitem", name="/", exact=True).get_by_label("gitmanager_stage_button").click()
        time.sleep(1)

    def create_commit(self, commit_message: str):
        """Создаёт коммит с указанным сообщением"""
        self.page.get_by_role("textbox", name="commit").fill(commit_message)
        time.sleep(1)
        self.page.get_by_role("button", name="gitmanager_commit_button").click()
        self.page.get_by_text("Выполнен commitСоздан коммит").wait_for(state="visible", timeout=10000)
        time.sleep(1)

    def commit_all_changes(self, commit_message: str):
        """Полный цикл: открыть панель, поставить в stage, создать коммит"""
        self.open_commit_panel()
        self.stage_all_files()
        self.create_commit(commit_message)

