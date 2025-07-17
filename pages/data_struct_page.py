from playwright.sync_api import Page
from .base_page import BasePage
import time

class DataStructPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    # --- Основные селекторы ---
    NAME_INPUT = 'input[aria-label="Имя структуры данных"]'  # уточнить селектор
    DESCRIPTION_INPUT = 'input[aria-label="Описание структуры данных"]'  # уточнить селектор
    ADD_ATTR_BUTTON = 'button:has-text("+")'  # кнопка добавления атрибута
    ATTR_NAME_INPUT = 'input[placeholder="Атрибут"]'  # уточнить селектор
    ATTR_TYPE_SELECT = 'select'  # селектор типа (dropdown)
    ATTR_DESC_INPUT = 'input[placeholder="Описание"]'  # уточнить селектор
    DELETE_ATTR_BUTTON = 'button[aria-label="Удалить атрибут"]'  # уточнить селектор
    GENERATE_PYTHON_BUTTON = 'button:has-text("Генерировать python-классы")'
    SAVE_BUTTON = 'button:has-text("Сохранить")'  # если есть явная кнопка

    # --- Методы для левой панели ---
    CREATE_SCHEMA_BUTTON = 'button[aria-label="datastructureeditor_create_schema_button"]'
    SEARCH_SCHEMA_BUTTON = 'button[aria-label="datastructureeditor_search_schemas_button"]'
    GENERATE_BUTTON = 'button[aria-label="datastructureeditor_generate_button"]'
    TREE_ITEM = 'div[role="treeitem"]'
    TREE = 'div[role="tree"]'
    RENAME_SCHEMA_BUTTON = 'button[aria-label="datastructureeditor_rename_schema_button"]'
    DELETE_SCHEMA_BUTTON = 'button[aria-label="datastructureeditor_delete_schema_button"]'
    DRAGGER = 'button[aria-label="dragger"]'

    # --- Методы для правой части (атрибуты структуры) ---
    DESCRIPTION_TEXTAREA = 'textarea[aria-label="description"]'
    ADD_ATTRIBUTE_BUTTON = 'button[aria-label="datastructureeditor_create_attribute_button"]'
    SEARCH_ATTRIBUTE_BUTTON = 'button[aria-label="datastructureeditor_search_attributes_button"]'
    ATTRIBUTE_ROW = 'li.SortableItem__SortableItem___ni0ge'

    def set_name(self, name: str):
        self.page.fill(self.NAME_INPUT, name)

    def set_description(self, description: str):
        self.page.fill(self.DESCRIPTION_INPUT, description)

    def add_attribute(self, name: str, attr_type: str = "string", description: str = ""):
        self.page.click(self.ADD_ATTR_BUTTON)
        attr_rows = self.page.query_selector_all('tr')
        last_row = attr_rows[-1]
        name_input = last_row.query_selector('input[placeholder="Атрибут"]')
        type_select = last_row.query_selector('select')
        desc_input = last_row.query_selector('input[placeholder="Описание"]')
        if name_input is None or type_select is None or desc_input is None:
            raise Exception(f"Не найден один из инпутов атрибута: name_input={name_input}, type_select={type_select}, desc_input={desc_input}")
        name_input.fill(name)
        type_select.select_option(attr_type)
        if description:
            desc_input.fill(description)

    def delete_attribute(self, index: int = -1):
        attr_rows = self.page.query_selector_all('tr')
        row = attr_rows[index]
        del_btn = row.query_selector('button[aria-label="Удалить атрибут"]')
        if del_btn is None:
            raise Exception("Кнопка удаления атрибута не найдена!")
        del_btn.click()

    def edit_attribute(self, index: int, name: str = None, attr_type: str = None, description: str = None):
        attr_rows = self.page.query_selector_all('tr')
        row = attr_rows[index]
        if name is not None:
            name_input = row.query_selector('input[placeholder="Атрибут"]')
            if name_input is None:
                raise Exception("Инпут имени атрибута не найден!")
            name_input.fill(name)
        if attr_type is not None:
            type_select = row.query_selector('select')
            if type_select is None:
                raise Exception("Селектор типа атрибута не найден!")
            type_select.select_option(attr_type)
        if description is not None:
            desc_input = row.query_selector('input[placeholder="Описание"]')
            if desc_input is None:
                raise Exception("Инпут описания атрибута не найден!")
            desc_input.fill(description)

    def generate_python_classes(self):
        self.page.click(self.GENERATE_PYTHON_BUTTON)

    def save(self):
        self.page.click(self.SAVE_BUTTON)

    def get_error_messages(self):
        # Возвращает список текстов ошибок валидации
        return [el.inner_text() for el in self.page.query_selector_all('.error-message, .ErrorMessage')]

    def create_schema(self, name: str):
        self.page.click(self.CREATE_SCHEMA_BUTTON)
        # Ожидаем появления инпута для имени (может быть input или textarea)
        self.page.wait_for_selector('input, textarea', timeout=3000)
        input_box = self.page.query_selector('input, textarea')
        if input_box is None:
            raise Exception('Инпут для имени новой структуры не найден!')
        input_box.fill(name)
        self.page.keyboard.press('Enter')
        self.page.wait_for_selector(f'{self.TREE_ITEM}[aria-label="{name}"]', timeout=3000)

    def delete_schema(self, name: str):
        item = self.page.query_selector(f'{self.TREE_ITEM}[aria-label="{name}"]')
        if item is None:
            raise Exception(f'Структура данных с именем {name} не найдена!')
        # Кнопка удаления внутри item
        del_btn = item.query_selector(self.DELETE_SCHEMA_BUTTON)
        if del_btn is None:
            raise Exception('Кнопка удаления структуры не найдена!')
        del_btn.click()
        # Подтверждение (если появляется модалка)
        try:
            self.page.get_by_role('button', name='Удалить').click()
        except Exception:
            pass  # если нет подтверждения
        self.page.wait_for_selector(f'{self.TREE_ITEM}[aria-label="{name}"]', state='detached', timeout=3000)

    def rename_schema(self, old_name: str, new_name: str):
        item = self.page.query_selector(f'{self.TREE_ITEM}[aria-label="{old_name}"]')
        if item is None:
            raise Exception(f'Структура данных с именем {old_name} не найдена!')
        rename_btn = item.query_selector(self.RENAME_SCHEMA_BUTTON)
        if rename_btn is None:
            raise Exception('Кнопка переименования структуры не найдена!')
        rename_btn.click()
        self.page.wait_for_selector('input, textarea', timeout=3000)
        input_box = self.page.query_selector('input, textarea')
        if input_box is None:
            raise Exception('Инпут для переименования не найден!')
        input_box.fill(new_name)
        self.page.keyboard.press('Enter')
        self.page.wait_for_selector(f'{self.TREE_ITEM}[aria-label="{new_name}"]', timeout=3000)

    def search_schema(self, query: str):
        self.page.click(self.SEARCH_SCHEMA_BUTTON)
        self.page.wait_for_selector('input, textarea', timeout=3000)
        input_box = self.page.query_selector('input, textarea')
        if input_box is None:
            raise Exception('Инпут поиска не найден!')
        input_box.fill(query)
        self.page.keyboard.press('Enter')
        # Можно вернуть список найденных структур
        return [el.get_attribute('aria-label') for el in self.page.query_selector_all(self.TREE_ITEM)]

    def generate_python_classes_left(self):
        self.page.click(self.GENERATE_BUTTON)
        # Можно добавить ожидание уведомления или другого признака успеха

    def drag_left_panel(self, offset: int = 50):
        dragger = self.page.query_selector(self.DRAGGER)
        if dragger is None:
            raise Exception('Dragger не найден!')
        box = dragger.bounding_box()
        if box is None:
            raise Exception('Не удалось получить bounding box dragger!')
        self.page.mouse.move(box['x'] + box['width'] // 2, box['y'] + box['height'] // 2)
        self.page.mouse.down()
        self.page.mouse.move(box['x'] + box['width'] // 2 + offset, box['y'] + box['height'] // 2)
        self.page.mouse.up()

    def set_struct_description(self, text: str):
        self.page.fill(self.DESCRIPTION_TEXTAREA, text)

    def add_attribute_right(self, name: str, attr_type: str = "string", description: str = ""):
        self.page.click(self.ADD_ATTRIBUTE_BUTTON)
        # Находим последний атрибут
        rows = self.page.query_selector_all(self.ATTRIBUTE_ROW)
        last = rows[-1]
        name_input = last.query_selector('input[aria-label^="attributes."]')
        type_textarea = last.query_selector('textarea[aria-label$="schema.type"]')
        desc_textarea = last.query_selector('textarea[aria-label$="schema.description"]')
        if name_input is None or type_textarea is None or desc_textarea is None:
            raise Exception("Не найден один из инпутов атрибута!")
        name_input.fill(name)
        type_textarea.fill(attr_type)
        desc_textarea.fill(description)

    def edit_attribute_right(self, index: int, name: str = None, attr_type: str = None, description: str = None):
        rows = self.page.query_selector_all(self.ATTRIBUTE_ROW)
        row = rows[index]
        if name is not None:
            name_input = row.query_selector('input[aria-label^="attributes."]')
            if name_input is None:
                raise Exception("Инпут имени не найден!")
            name_input.fill(name)
        if attr_type is not None:
            type_textarea = row.query_selector('textarea[aria-label$="schema.type"]')
            if type_textarea is None:
                raise Exception("Textarea типа не найдена!")
            type_textarea.fill(attr_type)
        if description is not None:
            desc_textarea = row.query_selector('textarea[aria-label$="schema.description"]')
            if desc_textarea is None:
                raise Exception("Textarea описания не найдена!")
            desc_textarea.fill(description)

    def delete_attribute_right(self, index: int):
        rows = self.page.query_selector_all(self.ATTRIBUTE_ROW)
        row = rows[index]
        del_btn = row.query_selector('button[aria-label="datastructureeditor_delete_attribute_button"]')
        if del_btn is None:
            raise Exception("Кнопка удаления атрибута не найдена!")
        del_btn.click()

    def set_attribute_required(self, index: int, required: bool = True):
        rows = self.page.query_selector_all(self.ATTRIBUTE_ROW)
        row = rows[index]
        req_btn = row.query_selector('button[aria-label="datastructureeditor_required_attribute_button"]')
        if req_btn is None:
            raise Exception("Кнопка обязательности не найдена!")
        # Клик только если состояние не совпадает (визуально можно проверить класс или атрибут)
        req_btn.click()

    def open_attribute_settings(self, index: int):
        rows = self.page.query_selector_all(self.ATTRIBUTE_ROW)
        row = rows[index]
        settings_btn = row.query_selector('button[aria-label="datastructureeditor_settings_attribute_button"]')
        if settings_btn is None:
            raise Exception("Кнопка настроек не найдена!")
        settings_btn.click()

    def drag_attribute(self, from_index: int, to_index: int):
        rows = self.page.query_selector_all(self.ATTRIBUTE_ROW)
        from_row = rows[from_index]
        to_row = rows[to_index]
        drag_handle = from_row.query_selector('[aria-roledescription="sortable"]')
        if drag_handle is None:
            raise Exception("Drag handle не найден!")
        box = drag_handle.bounding_box()
        if box is None:
            raise Exception("Не удалось получить bounding box drag handle!")
        to_box = to_row.bounding_box()
        if to_box is None:
            raise Exception("Не удалось получить bounding box целевого row!")
        self.page.mouse.move(box['x'] + box['width']//2, box['y'] + box['height']//2)
        self.page.mouse.down()
        self.page.mouse.move(to_box['x'] + to_box['width']//2, to_box['y'] + to_box['height']//2)
        self.page.mouse.up()

    def search_attribute(self, query: str):
        self.page.click(self.SEARCH_ATTRIBUTE_BUTTON)
        self.page.wait_for_selector('input, textarea', timeout=3000)
        input_box = self.page.query_selector('input, textarea')
        if input_box is None:
            raise Exception('Инпут поиска по атрибутам не найден!')
        input_box.fill(query)
        self.page.keyboard.press('Enter')
        # Вернуть список найденных атрибутов
        return [el.query_selector('input[aria-label^="attributes."]').input_value() for el in self.page.query_selector_all(self.ATTRIBUTE_ROW)] 