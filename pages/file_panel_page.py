from playwright.sync_api import Page
from .base_page import BasePage
import time

class FilePanelPage(BasePage):
    TREE_ITEM_SELECTOR = 'div[role="treeitem"][aria-label="/{name}"]'
    DELETE_BTN_SELECTOR = 'div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Удалить")'
    MENUITEM_SELECTOR = 'div[role="menuitem"], div.TreeItem__LabelPrimary___vzajD'
    CONFIRM_DELETE_BTN_SELECTOR = 'button[role="button"], button'
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

    def click_toolbar_filemanager_button(self):
        self.page.get_by_role("button", name="board_toolbar_filemanager_button").click()

    def click_create_file_button(self):
        self.page.get_by_role("button", name="filemanager_create_button").click()

    def click_data_structure_type(self):
        self.page.wait_for_selector('div[role="menu"] div, div[role="menuitem"], div.TreeItem__LabelPrimary___vzajD', timeout=5000)
        self.page.get_by_text("Структуры данных", exact=True).click()

    def fill_treeitem_label_field(self, value):
        self.page.get_by_role("textbox", name="treeitem_label_field").fill(value)

    def press_enter_treeitem_label_field(self):
        self.page.get_by_role("textbox", name="treeitem_label_field").press("Enter")

    def click_create_schema_button(self):
        self.page.get_by_role("button", name="datastructureeditor_create_schema_button").click()

    def click_treeitem_label_field(self):
        self.page.get_by_role("textbox", name="treeitem_label_field").click()

    def fill_schema_name(self, value):
        self.page.get_by_role("textbox", name="treeitem_label_field").fill(value)

    def press_enter_schema_name(self):
        self.page.get_by_role("textbox", name="treeitem_label_field").press("Enter")

    def fill_schema_description(self, value):
        self.page.get_by_role("textbox", name="description").fill(value)

    def click_create_attribute_button(self):
        self.page.get_by_role("button", name="datastructureeditor_create_attribute_button").click()

    def fill_attribute_name(self, value):
        self.page.get_by_role("textbox", name="attributes.0.name").fill(value)

    def press_enter_attribute_name(self):
        self.page.get_by_role("textbox", name="attributes.0.name").press("Enter")

    def click_type_dropdown(self):
        self.page.get_by_role("button", name="textfield_arrow_button").click()

    def click_type_dropdown_force(self):
        self.page.get_by_role("button", name="textfield_arrow_button").click(force=True)

    def click_type_string(self):
        self.page.get_by_text("string").click()

    def click_attribute_description(self):
        self.page.get_by_role("textbox", name="attributes.0.schema.description").click()

    def fill_attribute_description(self, value):
        self.page.get_by_role("textbox", name="attributes.0.schema.description").fill(value)

    def click_required_attribute_button(self):
        self.page.get_by_role("button", name="datastructureeditor_required_attribute_button").click()

    def click_required_attribute_button_by_index(self, idx):
        # Находим все контейнеры атрибутов (listitem)
        attr_blocks = self.page.query_selector_all('li[data-testid="datastructureeditor_attribute_item"]')
        if idx >= len(attr_blocks):
            raise AssertionError(f'Нет блока атрибута с индексом {idx}')
        block = attr_blocks[idx]
        btn = block.query_selector('button[aria-label="datastructureeditor_required_attribute_button"]')
        if not btn:
            raise AssertionError(f'Не найдена кнопка "Обязательный атрибут" в блоке {idx}')
        btn.click()

    def create_folder(self, base_name):
        existing_names = set(self.get_all_tree_names())
        folder_name = self._generate_unique_name(base_name, existing_names)
        self.open_create_file_menu()
        time.sleep(1)
        folder_btn = None
        folder_btns = self.page.query_selector_all('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]')
        for btn in folder_btns:
            if btn.inner_text().strip() == 'Папку':
                folder_btn = btn
                break
        if not folder_btn:
            print("[FAIL] Кнопка 'Папку' не найдена!")
            return None
        try:
            self.create_file_or_folder_of_type(folder_btn, folder_name)
            print(f"[OK] Папка '{folder_name}' создана успешно!")
            return folder_name
        except Exception as e:
            print(f"[FAIL] Не удалось создать папку '{folder_name}': {e}")
            return None

    def create_file_of_type(self, base_name, aria, text, extension=None):
        self.open_create_file_menu()
        found_btn = None
        for btn in self.get_file_type_buttons():
            if btn.get_attribute('aria-label') == aria and btn.inner_text() == text:
                found_btn = btn
                break
        if not found_btn:
            print(f"[SKIP] Не найден тип: aria-label={aria}, text={text}")
            return None
        file_name = f"{base_name}_{int(time.time())}"
        self.create_file_or_folder_of_type(found_btn, file_name)
        return file_name

    def _generate_unique_name(self, base, existing_names):
        idx = 1
        name = base
        while name in existing_names:
            name = f"{base}_{idx}"
            idx += 1
        return name

    def create_data_structure_file(self):
        self.open_create_file_menu()
        self.click_data_structure_type()
        file_name = f"datastruct_{int(time.time())}"
        self.fill_treeitem_label_field(file_name)
        self.press_enter_treeitem_label_field()
        return file_name

    def create_openapi_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "openapi" in (aria or '').lower() or "openapi" in (text or '').lower():
                base_name = f"openapi_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'OpenAPI' не найдена!")
        return None

    def create_config_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "config" in (aria or '').lower() or "config" in (text or '').lower():
                base_name = f"config_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'Config' не найдена!")
        return None

    def create_process_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "процесс" in (aria or '').lower() or "процесс" in (text or '').lower():
                base_name = f"process_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'Процесс' не найдена!")
        return None

    def create_python_script_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "python" in (aria or '').lower() or "python" in (text or '').lower():
                base_name = f"py_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'Скрипт Python' не найдена!")
        return None

    def create_decision_table_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "таблица решений" in (aria or '').lower() or "таблица решений" in (text or '').lower():
                base_name = f"decision_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'Таблица решений' не найдена!")
        return None

    def create_test_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "тест" in (aria or '').lower() or "тест" in (text or '').lower():
                base_name = f"test_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'Тест' не найдена!")
        return None

    def create_db_connection_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "бд" in (aria or '').lower() or "бд" in (text or '').lower() or "database" in (aria or '').lower() or "database" in (text or '').lower():
                base_name = f"db_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'Подключение к БД' не найдена!")
        return None

    def create_file_file(self):
        file_type_buttons = self.get_file_type_buttons()
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if "файл" in (aria or '').lower() or "файл" in (text or '').lower():
                base_name = f"file_{int(time.time())}"
                return self.create_file_of_type(base_name, aria, text, extension)
        print("[FAIL] Кнопка типа 'Файл' не найдена!")
        return None

    def delete_tree_item(self, name, timeout=10000):
        selector = self.TREE_ITEM_SELECTOR.format(name=name)
        treeitem = self.page.query_selector(selector)
        if not treeitem:
            raise AssertionError(f'Не найден элемент для удаления: {name}')
        self.page.evaluate('(el) => el.scrollIntoView({block: "center"})', treeitem)
        treeitem.click(button='right')
        self.page.wait_for_selector(self.MENUITEM_SELECTOR, timeout=3000)
        delete_btn = self.page.query_selector(self.DELETE_BTN_SELECTOR)
        if not delete_btn:
            raise AssertionError(f'Не найдена кнопка удаления для: {name}')
        delete_btn.click()
        self.page.wait_for_selector(self.CONFIRM_DELETE_BTN_SELECTOR, timeout=5000)
        self.page.get_by_role("button", name="Удалить").click()
        self.page.wait_for_selector(selector, state='detached', timeout=timeout)
        assert not self.page.query_selector(selector), f'Файл {name} не был удалён!' 

    def select_attribute_type(self, type_name):
        # Клик по полю типа
        self.page.click('textarea[name="attributes.0.schema.type"]')
        # Клик по стрелке (force)
        self.page.click('button[aria-label="textfield_arrow_button"]', force=True)
        # Сразу жду появления нужного типа и кликаю по нему
        self.page.wait_for_selector(f'div[role="treeitem"][aria-label="{type_name}"]', timeout=7000)
        self.page.get_by_role("treeitem", name=type_name).click() 

    def fill_attribute_description_by_index(self, idx, value):
        # Находит поле описания по индексу и заполняет его, если оно есть
        locator = self.page.get_by_role("textbox", name=f"attributes.{idx}.schema.description")
        if locator.count():
            locator.fill(value)
        else:
            print(f"[WARN] Поле описания для attributes.{idx}.schema.description не найдено, пропускаем.")

    def select_attribute_type_by_index(self, idx, type_name):
        # Клик по полю типа с нужным индексом
        self.page.get_by_role("textbox", name=f"attributes.{idx}.schema.type").click()
        self.page.wait_for_selector(f'div[role="treeitem"][aria-label="{type_name}"]', timeout=5000)
        self.page.locator(f'div[role="treeitem"][aria-label="{type_name}"]').click() 

    def select_list_element_type_in_modal(self, element_type):
        # Ожидаем появления видимой модалки выбора типа для list
        modal = self.page.locator('div[role="dialog"]:visible')
        modal.wait_for(timeout=5000)
        # Кликаем по селекту типа элемента внутри этой модалки
        modal.get_by_role("combobox").click()
        # Ждём и выбираем нужный тип
        modal.locator(f'div[role="option"], div[role="treeitem"][aria-label="{element_type}"]').first.click()
        # Подтверждаем выбор
        modal.get_by_role("button", name="Выбрать").click()

    def select_dict_key_value_types_in_modal(self, key_type, value_type):
        # Ожидаем появления видимой модалки выбора типов для dictionary
        modal = self.page.locator('div[role="dialog"]:visible')
        modal.wait_for(timeout=5000)
        # Первый combobox — ключ, второй — значение
        comboboxes = modal.get_by_role('combobox')
        comboboxes.nth(0).click()
        modal.locator(f'div[role="option"], div[role="treeitem"][aria-label="{key_type}"]').first.click()
        comboboxes.nth(1).click()
        modal.locator(f'div[role="option"], div[role="treeitem"][aria-label="{value_type}"]').first.click()
        # Подтверждаем выбор
        modal.get_by_role("button", name="Выбрать").click() 