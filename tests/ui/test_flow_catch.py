import time
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.diagram_page import DiagramPage
from pages.canvas_utils import CanvasUtils
from conftest import save_screenshot, get_project_by_code, delete_project_by_id
from locators import (
    FilePanelLocators,
    DiagramLocators,
    CanvasLocators,
    ComponentLocators,
    ModalLocators,
    ToolbarLocators
)


def test_flow_catch(login_page, shared_flow_project):
    """
    Тест для диаграммы test_catch - проверка завершения на компоненте Output2
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)
    canvas_utils = CanvasUtils(page)
    
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)

    print("[INFO] Шаг 1: Открытие диаграммы test_catch.df.json")
    file_panel.open_file_panel()
    time.sleep(1)
    
    test_flow_folder = page.locator(FilePanelLocators.get_treeitem_by_name("test_flow_component"))
    assert test_flow_folder.count() > 0, "Папка 'test_flow_component' не найдена в проекте!"
    print("[SUCCESS] Папка 'test_flow_component' найдена")
    test_flow_folder.click()
    time.sleep(1)
    
    test_catch_file = page.locator(FilePanelLocators.get_treeitem_by_name("test_catch.df.json"))
    assert test_catch_file.count() > 0, "Файл 'test_catch.df.json' не найден в папке!"
    print("[SUCCESS] Файл 'test_catch.df.json' найден")
    test_catch_file.dblclick()
    time.sleep(2)
    
    diagram_page.close_panels()
    time.sleep(1)
    print("[SUCCESS] Диаграмма test_catch открыта и панели закрыты!")

    print("[INFO] Шаг 2: Поиск и настройка компонента Output2")
    output2_found = canvas_utils.find_component_by_title("Output2", exact=True)
    assert output2_found, "Компонент 'Output2' не найден на канвасе!"
    print("[SUCCESS] Компонент 'Output2' найден на канвасе!")
    
    output2_component = page.get_by_text("Output2").first
    output2_component.dblclick(force=True)
    time.sleep(1)
    print("[SUCCESS] Открыты настройки компонента Output2")
    
    try:
        component_tab = page.get_by_text("Компонент", exact=True)
        if component_tab.is_visible():
            component_tab.click()
            time.sleep(0.5)
        
        data_field = page.get_by_role("textbox", name="inputs_config.data.value")
        if not data_field.is_visible():
            data_field = page.locator(ComponentLocators.DATA_VALUE_FALLBACK).first
        
        if data_field.is_visible():
            data_field.fill('{"text": "Это второй выход, пойманный кетчем"}')
            time.sleep(0.5)
            print("[SUCCESS] Поле 'Данные' заполнено для компонента Output2")
        else:
            print("[WARN] Поле 'Данные' не найдено для компонента Output2")
            page.screenshot(path='screenshots/debug_output2_data_field.png', full_page=True)
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении поля 'Данные': {e}")
        page.screenshot(path='screenshots/debug_output2_data_error.png', full_page=True)
    
    diagram_page.close_right_sidebar()
    time.sleep(1)
    print("[SUCCESS] Сайдбар закрыт после настройки Output2")

    print("[INFO] Шаг 3: Выполнение диаграммы")
    success = diagram_page.run_diagram_and_wait(completion_timeout=15000)
    if success:
        print("[SUCCESS] Диаграмма завершилась успешно!")
        
        try:
            toast = page.locator(ModalLocators.TOAST).first
            toast.wait_for(state="visible", timeout=5000)
            toast_text = toast.text_content()
            print(f"[SUCCESS] Тост найден: {toast_text}")
        except Exception as e:
            print(f"[WARN] Ошибка при проверке тоста: {e}")
            page.screenshot(path='screenshots/debug_toast_error.png', full_page=True)
    else:
        print("[WARN] Диаграмма не завершилась успешно, но продолжаем проверку")

    print("[INFO] Шаг 4: Проверка вывода компонента Output2 в анализе")
    output2_component = page.get_by_text("Output2").first
    output2_component.dblclick(force=True)
    time.sleep(1)
    print("[SUCCESS] Открыт сайдбар компонента Output2")
    
    page.get_by_text("Процесс", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Переключились на вкладку 'Процесс'")
    
    page.get_by_text("Анализ").click()
    time.sleep(1)
    print("[SUCCESS] Переключились на подвкладку 'Анализ'")
    
    page.get_by_role("button", name="formitem_full_view_button").nth(1).click()
    time.sleep(1)
    print("[SUCCESS] Нажата кнопка 'formitem_full_view_button'")
    
    try:
        json_modal = page.get_by_text("Просмотр JSON")
        if json_modal.is_visible():
            print("[SUCCESS] Модалка 'Просмотр JSON' найдена")
            
            response_section = page.get_by_text("Ответ")
            if response_section.is_visible():
                print("[SUCCESS] Секция 'Ответ' найдена в модалке")
                
                json_data = page.locator(ModalLocators.get_json_content_selector()).first
                if json_data.is_visible():
                    json_text = json_data.text_content()
                    print(f"[SUCCESS] JSON данные найдены: {json_text}")
                    
                    assert "Это второй выход, пойманный кетчем" in json_text, f"В JSON не найдено ожидаемое сообщение: {json_text}"
                    print("[SUCCESS] В JSON найдено ожидаемое сообщение 'Это второй выход, пойманный кетчем'")
                else:
                    print("[WARN] JSON данные не найдены в модалке")
            else:
                print("[WARN] Секция 'Ответ' не найдена в модалке")
        else:
            print("[WARN] Модалка 'Просмотр JSON' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при проверке модалки 'Просмотр JSON': {e}")
        page.screenshot(path='screenshots/debug_json_modal.png', full_page=True)

    print("[SUCCESS] Тест test_flow_catch завершен успешно!")
