import time
import pytest
from pages.file_panel_page import FilePanelPage
from pages.project_page import ProjectPage
from pages.data_struct_page import DataStructPage

def test_create_schema_with_struct_refs(login_page):
    page = login_page
    file_panel = FilePanelPage(page)
    project_page = ProjectPage(page)
    data_struct = DataStructPage(page)
    project_page.goto_first_available_project()
    file_panel.click_toolbar_filemanager_button()
    time.sleep(0.5)
    file_panel.click_create_file_button()
    time.sleep(0.5)
    file_panel.click_data_structure_type()
    time.sleep(0.5)
    file_name = f"datastruct_{int(time.time())}"
    file_panel.fill_treeitem_label_field(file_name)
    file_panel.press_enter_treeitem_label_field()
    time.sleep(0.5)
    page.get_by_role("button", name="Создать").click()
    schema1_name = f"schema1_{int(time.time())}"
    page.get_by_role("textbox", name="treeitem_label_field").fill(schema1_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    time.sleep(1)
    schema2_name = f"schema2_{int(time.time())}"
    data_struct.create_schema(schema2_name)
    time.sleep(1)
    page.get_by_role("treeitem", name=schema2_name).click()
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