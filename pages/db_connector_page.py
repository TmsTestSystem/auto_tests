from playwright.sync_api import Page
from .base_page import BasePage
import time

class DBConnectorPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    # Селекторы для работы с DB connector
    DB_CONNECTION_TREEITEM = 'treeitem[name="database_connection_info"]'
    TYPE_SELECTOR = 'textbox[name="type"]'
    POOL_SIZE_SELECTOR = 'textbox[name="pool_size"]'
    CONNECTION_STRING_SELECTOR = 'textbox[name="connection.conn_str"]'
    TEST_CONNECTION_BUTTON = 'button[name="test_connection"]'
    SUBMIT_BUTTON = 'button[name="dbconnection_submit"]'
    CONNECTION_SUCCESS_MESSAGE = 'div:has-text("Подключение установлено")'

    def create_db_connector_file(self, file_name: str):
        """Создает файл подключения к БД"""
        try:
            self.page.get_by_role("treeitem", name="database_connection_info").locator("div").nth(2).click()
            # Ждём появления поля для ввода имени файла
            self.page.wait_for_selector('input[name="treeitem_label_field"]', timeout=5000)
            self.page.fill('input[name="treeitem_label_field"]', file_name)
            self.page.keyboard.press('Enter')
            time.sleep(1)
            return True
        except Exception as e:
            self.page.screenshot(path=f'screenshots/db_treeitem_fail_{int(time.time())}.png', full_page=True)
            raise Exception(f"Не удалось создать файл-коннектор к БД: {e}")

    def configure_connection_string(self, connection_string: str = "$env.DATABASE_URL", pool_size: str = "10"):
        """Настраивает подключение к БД через строку подключения"""
        # 1. В поле "Тип подключения" выбрать "Строка подключения"
        self.page.get_by_role("textbox", name="type").click()
        self.page.get_by_text("Строка подключения").click()
        
        # 2. Заполнить поле пул сайз значением
        self.page.get_by_role("textbox", name="pool_size").fill(pool_size)
        
        # 3. Заполнить поле "Строка подключения"
        self.page.get_by_role("textbox", name="connection.conn_str").fill(connection_string)

    def test_connection(self, timeout: int = 10000):
        """Проверяет подключение к БД"""
        # 4. Нажать на кнопку "Проверить подключение"
        test_button = self.page.get_by_role("button", name="test_connection")
        if not test_button.is_visible():
            raise Exception("Кнопка 'Проверить подключение' не найдена!")
        test_button.click()
        
        # Ждем немного для обработки запроса
        time.sleep(2)
        
        # Проверяем наличие ошибки подключения
        error_message = self.page.locator('div:has-text("Ошибка подключения"), div:has-text("Connection failed"), div:has-text("Error")')
        if error_message.count() > 0:
            error_text = error_message.first.inner_text()
            self.page.screenshot(path=f'screenshots/db_connection_error_{int(time.time())}.png', full_page=True)
            raise Exception(f"Ошибка подключения к БД: {error_text}")
        
        # 5. Проверить наличие успешной нотификации
        try:
            self.page.wait_for_selector(self.CONNECTION_SUCCESS_MESSAGE, timeout=timeout)
        except Exception as e:
            # Делаем скриншот для диагностики
            self.page.screenshot(path=f'screenshots/db_connection_timeout_{int(time.time())}.png', full_page=True)
            raise Exception(f"Не удалось подтвердить успешное подключение к БД. Timeout: {e}")

    def save_connection(self):
        """Сохраняет настройки подключения"""
        # 6. Нажать на кнопку "Сохранить"
        self.page.get_by_role("button", name="dbconnection_submit").click()
        time.sleep(1)

    def configure_and_save_connection(self, connection_string: str = "$env.DATABASE_URL", pool_size: str = "10"):
        """Полный цикл настройки и сохранения подключения"""
        self.configure_connection_string(connection_string, pool_size)
        self.test_connection()
        self.save_connection() 