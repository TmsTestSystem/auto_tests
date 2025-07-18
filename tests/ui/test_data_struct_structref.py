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
    # Переход в первый доступный проект
    project_page.goto_first_available_project()
    # 1. Открыть файловую панель и создать первую структуру данных (на которую будут ссылки)
    file_panel.click_toolbar_filemanager_button()
    time.sleep(0.5)
    file_panel.click_create_file_button()
    time.sleep(0.5)
    file_panel.click_data_structure_type()
    time.sleep(0.5)
    base_schema_name = f"schema_{int(time.time())}"
    file_panel.fill_treeitem_label_field(base_schema_name)
    file_panel.press_enter_treeitem_label_field()
    time.sleep(0.5)
    page.get_by_role("button", name="Создать").click()
    page.get_by_role("textbox", name="treeitem_label_field").fill(base_schema_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    time.sleep(1)
    # 2. Создать вторую схему для ссылок
    ref_schema_name = f"schema_struct_ref_{int(time.time())}"
    data_struct.create_schema(ref_schema_name)
    time.sleep(1)
    # 3. Добавить атрибут типа 'Структура данных'
    data_struct.add_struct_ref_attribute(0, "ref_attr", base_schema_name)
    time.sleep(1)
    # 4. Добавить атрибут типа list(Структура данных)
    data_struct.add_list_struct_ref_attribute(1, "ref_list", base_schema_name)
    time.sleep(1)
    # 5. Добавить атрибут типа dictionary(Структура данных)
    data_struct.add_dict_struct_ref_attribute(2, "ref_dict", base_schema_name)
    time.sleep(1)
    # (Опционально) нажать "Генерировать python-классы"
    page.get_by_role("button", name="datastructureeditor_generate_button").click()
    time.sleep(2) 