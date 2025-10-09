import time
import pytest
from pages.file_panel_page import FilePanelPage
from pages.project_page import ProjectPage
from pages.data_struct_page import DataStructPage
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)

def test_create_schema_with_struct_refs(login_page):
    page = login_page
    file_panel = FilePanelPage(page)
    project_page = ProjectPage(page)
    data_struct = DataStructPage(page)
    project_page.goto_first_available_project()
    file_panel.open_file_panel()
    
    file_name = file_panel.create_data_structure_file()
    assert file_name is not None, "Не удалось создать файл структуры данных"
    
    page.locator(FilePanelLocators.get_treeitem_by_name(file_name)).click()
    time.sleep(1)
    
    schema1_name = f"schema1_{int(time.time())}"
    data_struct.create_schema(schema1_name)
    
    schema2_name = f"schema2_{int(time.time())}"
    data_struct.create_schema(schema2_name)
    
    data_struct.click_schema_in_tree(schema2_name)
    time.sleep(0.5)
    data_struct.click_create_attribute_button()
    time.sleep(0.5)
    data_struct.fill_attribute_name_by_index(0, "self_ref_attr")
    data_struct.press_enter_attribute_name_by_index(0)
    time.sleep(0.5)
    data_struct.select_attribute_type_by_index(0, "Структура данных")
    data_struct.select_schema_in_modal(schema2_name)
    time.sleep(1)
    data_struct.click_create_attribute_button()
    time.sleep(0.5)
    data_struct.fill_attribute_name_by_index(1, "list_schema2")
    data_struct.press_enter_attribute_name_by_index(1)
    time.sleep(0.5)
    data_struct.select_attribute_type_by_index(1, "list")
    data_struct.select_list_element_type_in_modal(schema2_name, is_first_list=True)
    time.sleep(1)
    data_struct.click_create_attribute_button()
    time.sleep(0.5)
    data_struct.fill_attribute_name_by_index(2, "dict_str_schema2")
    data_struct.press_enter_attribute_name_by_index(2)
    time.sleep(0.5)
    data_struct.select_attribute_type_by_index(2, "dictionary")
    data_struct.select_dict_key_value_types_in_modal("string", schema2_name)
    time.sleep(1)
    data_struct.generate_python_classes()
    time.sleep(2) 
