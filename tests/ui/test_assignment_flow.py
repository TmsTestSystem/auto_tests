import time
import pytest
from pages.file_panel_page import FilePanelPage
from pages.project_page import ProjectPage
from pages.data_struct_page import DataStructPage
from pages.diagram_page import DiagramPage
from pages.canvas_utils import CanvasUtils
from conftest import save_screenshot, get_project_by_code, delete_project_by_id
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


def test_assignment_flow(login_page, flow_project):
    """Тест для диаграммы test_assignment - создание переменных всех типов в компоненте Input"""
    page, project_code = flow_project
    
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)
    canvas_utils = CanvasUtils(page)
    
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)
    
    # Создание структуры данных
    file_panel.open_file_panel()
    file_name = file_panel.create_data_structure_file()
    assert file_name is not None, "Не удалось создать файл структуры данных"
    
    page.locator(FilePanelLocators.get_treeitem_by_name(file_name)).click()
    time.sleep(1)
    
    schema_name = f"test_schema_{int(time.time())}"
    data_struct = DataStructPage(page)
    data_struct.create_schema(schema_name)
    
    page.wait_for_selector('button[aria-label="datastructureeditor_create_attribute_button"]', timeout=10000)
    time.sleep(0.5)
    
    file_panel.fill_schema_description("Схема для тестирования")
    time.sleep(0.5)
    
    data_struct.click_create_attribute_button()
    page.wait_for_selector('input[name="attributes.0.name"]', timeout=10000)
    time.sleep(0.5)
    
    attr_name = f"test_string_attr_{int(time.time())}"
    data_struct.fill_attribute_name_by_index(0, attr_name)
    data_struct.press_enter_attribute_name_by_index(0)
    time.sleep(0.5)
    data_struct.fill_attribute_description_by_index(0, "Строковый атрибут")
    time.sleep(1)
    
    data_struct.generate_python_classes()
    time.sleep(2)
    
    # Открытие диаграммы
    test_flow_folder = page.locator(FilePanelLocators.get_treeitem_by_name("test_flow_component"))
    assert test_flow_folder.count() > 0, "Папка 'test_flow_component' не найдена!"
    test_flow_folder.click()
    time.sleep(1)
    
    test_assignment_file = page.locator(FilePanelLocators.get_treeitem_by_name("test_assignment.df.json"))
    assert test_assignment_file.count() > 0, "Файл 'test_assignment.df.json' не найден!"
    test_assignment_file.dblclick()
    time.sleep(2)
    
    diagram_page.close_panels()
    time.sleep(1)
    
    # Настройка Input компонента
    input_found = canvas_utils.find_component_by_title("Input", exact=True)
    assert input_found, "Компонент 'Input' не найден!"
    
    page.get_by_text("Input").first.dblclick()
    time.sleep(1)
    
    page.get_by_text("Процесс", exact=True).click()
    time.sleep(1)
    page.get_by_text("Параметры", exact=True).click()
    time.sleep(1)
    
    # Создание переменных
    variables_to_create = [
        {"name": "string", "type": "string", "is_complex": False},
        {"name": "integer", "type": "integer", "is_complex": False},
        {"name": "float", "type": "float", "is_complex": False},
        {"name": "boolean", "type": "boolean", "is_complex": False},
        {"name": "date", "type": "date", "is_complex": False},
        {"name": "datetime", "type": "datetime", "is_complex": False},
        {"name": "structure", "type": "structure", "is_complex": False},
        {"name": "list", "type": "list", "is_complex": True},
        {"name": "dictionary", "type": "dictionary", "is_complex": True}
    ]
    
    for i, var in enumerate(variables_to_create):
        page.locator(ComponentLocators.VARIABLES_CREATE_BUTTON).click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name=f"vars.{i}.name").fill(var['name'])
        time.sleep(0.5)
        
        page.locator(ComponentLocators.VARIABLES_ITEM_SETTINGS_BUTTON).nth(i).click()
        time.sleep(1)
        
        page.get_by_test_id("Modal__Container").get_by_role("textbox", name="schema.type").click()
        time.sleep(0.5)
        page.get_by_role("treeitem", name=var['type']).locator("div").nth(1).click()
        time.sleep(1)
        
        if var['type'] in ['structure', 'list', 'dictionary']:
            if var['is_complex']:
                page.get_by_role("textbox", name="popup.type").click()
                time.sleep(0.5)
                page.get_by_role("treeitem", name="structure").locator("div").nth(1).click()
                time.sleep(1)
            
            page.get_by_role("treeitem", name=f"/{file_name}").locator("div").nth(1).click()
            time.sleep(0.5)
            
            page.get_by_test_id("Modal__Container").locator("span").filter(has_text=schema_name).click()
            time.sleep(0.5)
            
            page.get_by_role("button", name="datastructureview_select_button").click()
            time.sleep(0.5)
            
            if var['is_complex']:
                page.get_by_role("button", name="datastructureeditor_popup_select_button").click()
                time.sleep(0.5)
        
        page.get_by_role("button", name="datastructureeditor_settings_submit_button").click()
        time.sleep(1)
    
    # Настройка Assignment компонента
    page.keyboard.press("Escape")
    time.sleep(1)
    
    assignment_found = canvas_utils.find_component_by_title("Assignment", exact=True)
    assert assignment_found, "Компонент 'Assignment' не найден!"
    
    page.get_by_text("Assignment").first.dblclick()
    time.sleep(1)
    
    variable_values = {
        "string": '"Тестовое строковое значение"',
        "integer": "42",
        "float": "3.14",
        "boolean": "true",
        "date": '"2024-01-01"',
        "datetime": '"2024-01-01T12:00:00Z"',
        "structure": '{"test_string_attr": "Значение для структуры"}',
        "list": '[{"test_string_attr": "Значение 1"}, {"test_string_attr": "Значение 2"}]',
        "dictionary": '{"key1": {"test_string_attr": "Значение 1"}, "key2": {"test_string_attr": "Значение 2"}}'
    }
    
    for i, var in enumerate(variables_to_create):
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name=f"config.assignments.{i}.target").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name=f"config.assignments.{i}.target").fill(f"$var.{var['name']}")
        time.sleep(1)
        
        page.get_by_role("textbox", name=f"config.assignments.{i}.value").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name=f"config.assignments.{i}.value").fill(variable_values[var['name']])
        time.sleep(1.5)
    
    page.keyboard.press("Escape")
    time.sleep(1)
    
    # Настройка Output компонента
    page.get_by_role("button", name="diagram_details_panel_switcher").click()
    time.sleep(1)
    
    output_found = canvas_utils.find_component_by_title("Output", exact=True)
    assert output_found, "Компонент 'Output' не найден!"
    
    page.get_by_text("Output").first.dblclick(force=True)
    time.sleep(1)
    
    output_data = "{"
    for i, var in enumerate(variables_to_create):
        if i > 0:
            output_data += ","
        output_data += f'"{var["name"]}": $node.Assignment.{var["name"]}'
    output_data += "}"
    
    page.get_by_role("textbox", name="config.data").click()
    time.sleep(0.5)
    page.get_by_role("textbox", name="config.data").fill(output_data)
    time.sleep(1)
    
    page.keyboard.press("Escape")
    time.sleep(1)
    
    # Запуск диаграммы
    page.get_by_role("button", name="diagram_play_button").click()
    time.sleep(3)
    
    # Проверка выполнения
    try:
        page.get_by_text("Диаграмма выполнена успешно").is_visible(timeout=10000)
    except:
        pass
    
    # Анализ результатов
    page.get_by_text("Анализ", exact=True).click()
    time.sleep(1)
    
    page.get_by_role("button", name="formitem_full_view_button").nth(1).click()
    time.sleep(1)
    
    json_contains_string = page.get_by_test_id("Modal__Container").get_by_text('"string": "Тестовое строковое значение"').is_visible(timeout=5000)
    assert json_contains_string, "JSON не содержит ожидаемого строкового значения!"
    
    page.keyboard.press("Escape")
    time.sleep(1)
    
    page.screenshot(path='screenshots/assignment_flow_completed.png', full_page=True)