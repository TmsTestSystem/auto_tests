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

    def wait_for_process_in_log(
        self,
        process_name: str,
        expected_status: str = "finished",
        *,
        timeout_sec: float = 90.0,
        poll_interval: float = 2.0,
        min_rows: int = 1,
        exact_rows: int | None = None,
    ) -> int:
        """
        Ждёт появления записи в журнале (строки подгружаются не сразу после execute).
        Возвращает итоговое число строк tbody.
        """
        deadline = time.monotonic() + timeout_sec
        last_detail = ""
        attempt = 0
        while time.monotonic() < deadline:
            attempt += 1
            # Периодически обновляем раздел — запись могла появиться на бэкенде, а список ещё старый
            if attempt > 1 and attempt % 4 == 0:
                try:
                    self.goto()
                except Exception:
                    pass
            try:
                log_table = self.page.locator("tbody.Table__Body___I87b4")
                log_table.wait_for(state="visible", timeout=8000)
                text = log_table.inner_text()
                n = log_table.locator("tr").count()
                if process_name not in text or expected_status.lower() not in text.lower():
                    last_detail = "нет процесса или статуса в тексте таблицы"
                elif n < min_rows:
                    last_detail = f"строк {n} < min_rows={min_rows}"
                elif exact_rows is not None and n != exact_rows:
                    last_detail = f"строк {n}, нужно ровно {exact_rows}"
                else:
                    return n
            except Exception as e:
                last_detail = str(e)
            time.sleep(poll_interval)
        raise AssertionError(
            f"За {timeout_sec}s в журнале не появилась запись {process_name!r} "
            f"со статусом {expected_status!r} (min_rows={min_rows}). Последняя проверка: {last_detail}"
        )

