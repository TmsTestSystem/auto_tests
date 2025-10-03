import time
import pytest
from pages.file_panel_page import FilePanelPage
from pages.project_page import ProjectPage
from pages.data_struct_page import DataStructPage

def test_create_data_struct_and_add_attribute(login_page):
    page = login_page
    file_panel = FilePanelPage(page)
    project_page = ProjectPage(page)
    data_struct = DataStructPage(page)
    project_page.goto_first_available_project()
    file_panel.open_file_panel()
    
    # Используем готовый метод для создания файла структуры данных
    file_name = file_panel.create_data_structure_file()
    assert file_name is not None, "Не удалось создать файл структуры данных"
    
    # Открываем созданный файл (кликаем по нему в дереве)
    page.get_by_role("treeitem", name=f"/{file_name}").click()
    time.sleep(1)
    
    # Создаем схему
    schema_name = f"schema_{int(time.time())}"
    data_struct.create_schema(schema_name)
    
    # Ждем появления кнопки создания атрибутов
    page.wait_for_selector('button[aria-label="datastructureeditor_create_attribute_button"]', timeout=10000)
    time.sleep(0.5)
    file_panel.fill_schema_description("Описание схемы автотестом")
    time.sleep(0.5)
    types = [
        "string",
        "boolean",
        "integer",
        "float",
        "date",
        "datetime"
    ]
    attr_idx = 0
    for type_name in types:
        data_struct.click_create_attribute_button()
        page.wait_for_selector(f'input[name="attributes.{attr_idx}.name"]', timeout=10000)
        time.sleep(0.5)
        attr_name = f"attr_{type_name}_{int(time.time())}"
        data_struct.fill_attribute_name_by_index(attr_idx, attr_name)
        data_struct.press_enter_attribute_name_by_index(attr_idx)
        time.sleep(0.5)
        if not (attr_idx == 0 and type_name == "string"):
            data_struct.select_attribute_type_by_index(attr_idx, type_name)
            time.sleep(0.5)
        data_struct.fill_attribute_description_by_index(attr_idx, f"Описание для {type_name}")
        time.sleep(1)
        attr_idx += 1
    data_struct.click_create_attribute_button()
    page.wait_for_selector(f'input[name="attributes.{attr_idx}.name"]', timeout=10000)
    time.sleep(0.5)
    attr_name = f"attr_list_string_{int(time.time())}"
    data_struct.fill_attribute_name_by_index(attr_idx, attr_name)
    data_struct.press_enter_attribute_name_by_index(attr_idx)
    time.sleep(0.5)
    data_struct.select_attribute_type_by_index(attr_idx, "list")
    data_struct.select_list_element_type_in_modal("string", is_first_list=True)
    data_struct.fill_attribute_description_by_index(attr_idx, "Описание для list[string]")
    time.sleep(1)
    attr_idx += 1
    data_struct.click_create_attribute_button()
    page.wait_for_selector(f'input[name="attributes.{attr_idx}.name"]', timeout=10000)
    time.sleep(0.5)
    attr_name = f"attr_dict_string_{int(time.time())}"
    data_struct.fill_attribute_name_by_index(attr_idx, attr_name)
    data_struct.press_enter_attribute_name_by_index(attr_idx)
    time.sleep(0.5)
    data_struct.select_attribute_type_by_index(attr_idx, "dictionary")
    data_struct.select_dict_key_value_types_in_modal("string", "string")
    data_struct.fill_attribute_description_by_index(attr_idx, "Описание для dict[string,string]")
    time.sleep(1)
    time.sleep(3)
    data_struct.generate_python_classes()
    time.sleep(2) 