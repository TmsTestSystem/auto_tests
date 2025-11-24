from playwright.sync_api import Page
from .base_page import BasePage
import time


class ProcessLogPage(BasePage):
    """Page Object для работы с журналом процессов"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    def goto(self):
        """Переход в журнал процессов"""
        self.page.get_by_role("link", name="Журнал процессов").click()
        self.page.wait_for_load_state("networkidle")

    def get_log_table(self):
        """Получает таблицу журнала процессов"""
        log_table = self.page.locator('tbody.Table__Body___I87b4')
        log_table.wait_for(state="visible", timeout=10000)
        return log_table

    def verify_process_in_log(self, process_name: str, expected_status: str = "finished"):
        """Проверяет наличие процесса в журнале с указанным статусом"""
        log_table = self.get_log_table()
        log_text = log_table.inner_text()
        assert process_name in log_text, f"В журнале нет процесса {process_name}"
        assert expected_status.lower() in log_text.lower(), f"Процесс не завершился со статусом {expected_status}"

    def get_log_rows_count(self):
        """Возвращает количество записей в журнале"""
        log_table = self.get_log_table()
        return log_table.locator("tr").count()

    def verify_log_rows_count(self, expected_count: int):
        """Проверяет количество записей в журнале"""
        actual_count = self.get_log_rows_count()
        assert actual_count == expected_count, f"В журнале ожидалось {expected_count} записей, найдено {actual_count}"

