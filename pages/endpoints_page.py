from playwright.sync_api import Page
from .base_page import BasePage
import time


class EndpointsPage(BasePage):
    """Page Object для работы с эндпоинтами"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    def open_endpoints_file(self):
        """Открывает файл endpoints.json"""
        self.page.get_by_text("config", exact=True).click()
        endpoints_treeitem = (
            self.page.get_by_label("/config/endpoints.json")
            .locator("div")
            .filter(has_text="endpoints.json")
            .nth(1)
        )
        endpoints_treeitem.wait_for(state="visible", timeout=10000)
        endpoints_treeitem.dblclick()
        time.sleep(2)

    def add_endpoint(self, alias: str, process_file: str):
        """Добавляет новый эндпоинт с указанным алиасом и файлом процесса"""
        self.page.get_by_role("button", name="endpoints_add_button").click()
        alias_input = self.page.get_by_role("textbox", name="endpoints.0.alias")
        alias_input.click()
        alias_input.fill(alias)
        file_select_button = self.page.get_by_role("button", name="textfield_select_file_button")
        file_select_button.click()
        
        # Выбор файла в модальном окне
        modal = self.page.get_by_test_id("Modal__Container")
        modal.get_by_role("treeitem", name=f"/{process_file}").locator("div").nth(1).click()
        self.page.get_by_role("button", name="filemanager_select_button").click()

    def save_endpoints(self):
        """Сохраняет эндпоинты и ждёт уведомления"""
        self.page.get_by_role("button", name="endpoints_submit").click()
        self.page.locator("div").filter(has_text="Эндпоинты сохранены").nth(2).wait_for(state="visible", timeout=10000)

