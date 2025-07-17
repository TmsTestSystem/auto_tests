from playwright.sync_api import Page
from .base_page import BasePage
import time

class FilePanelPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    def open_file_panel(self):
        self.page.wait_for_selector('button[aria-label="board_toolbar_filemanager_button"]', timeout=10000)
        self.page.click('button[aria-label="board_toolbar_filemanager_button"]')
        self.page.wait_for_selector('.Bar__Bar___lx-XI', timeout=10000)

    def open_create_file_menu(self):
        self.page.wait_for_selector('button[aria-label="filemanager_create_button"]', timeout=10000)
        self.page.click('button[aria-label="filemanager_create_button"]')
        self.page.wait_for_selector('.FilesMenu__FilesMenu___ESpN6', timeout=10000)

    def get_file_type_buttons(self):
        # Ищем кнопки типов файлов во всех меню и попапах
        buttons = []
        # Основное меню
        menu = self.page.query_selector('.FilesMenu__FilesMenu___ESpN6')
        if menu:
            buttons.extend(menu.query_selector_all('[role="treeitem"]'))
        # Все popups
        popups = self.page.query_selector_all('.Popup__Popup___vJ6BT')
        for popup in popups:
            buttons.extend(popup.query_selector_all('[role="treeitem"]'))
        return buttons

    def create_file_or_folder_of_type(self, file_type_button, file_name):
        time.sleep(0.5)
        file_type_button.click()
        input_selector = 'input[name="treeitem_label_field"]'
        time.sleep(0.5)
        self.page.wait_for_selector(input_selector, timeout=5000)
        input_box = self.page.query_selector(input_selector)
        if not input_box:
            screenshot_path = f'screenshots/diagnostic_no_input_{file_name}.png'
            self.page.screenshot(path=screenshot_path, full_page=True)
            print(f'[DIAG] Инпут для имени не найден! Скриншот: {screenshot_path}')
            print('[DIAG] HTML:')
            print(self.page.content())
            raise Exception('Input for file/folder name not found!')
        current_value = input_box.input_value()
        if current_value and current_value.strip() != '':
            time.sleep(0.5)
            input_box.fill('')
        time.sleep(0.5)
        input_box.fill(file_name)
        time.sleep(0.5)
        self.page.keyboard.press('Enter')
        time.sleep(0.5)
        self.page.wait_for_selector(input_selector, state='detached', timeout=5000)
        try:
            time.sleep(0.5)
            self.page.wait_for_selector(f'text={file_name}', timeout=5000)
            return True
        except Exception as e:
            screenshot_path = f'screenshots/diagnostic_autofile_{file_name}.png'
            self.page.screenshot(path=screenshot_path, full_page=True)
            print(f'[FAIL] Не удалось создать {file_name}: {e}. Скриншот: {screenshot_path}')
            print('[FAIL] HTML:')
            print(self.page.content())
            return False

    def get_all_tree_names(self):
        # Возвращает список имён всех файлов и папок в дереве (без слеша в начале)
        items = self.page.query_selector_all('div[role="treeitem"]')
        names = []
        for item in items:
            aria = item.get_attribute('aria-label')
            if aria and aria.startswith('/'):
                names.append(aria[1:])
        return names 