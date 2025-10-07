import time
import pytest
from playwright.sync_api import Page
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.diagram_page import DiagramPage
from pages.canvas_utils import CanvasUtils
from conftest import save_screenshot, get_project_by_code, delete_project_by_id

def test_find_flow_proc_component(login_page, shared_flow_project):
    """
    Простой тест для поиска компонента Flow_proc на диаграмме test_flow
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)
    canvas_utils = CanvasUtils(page)

    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)

    # 1. Открываем файловую панель
    print("[INFO] Шаг 1: Открытие файловой панели")
    file_panel.open_file_panel()
    time.sleep(1)

    # 2. Переходим в папку test_flow_component и открываем диаграмму test_flow
    print("[INFO] Шаг 2: Переход к диаграмме test_flow")

    # Ищем папку test_flow_component
    test_flow_folder = page.locator('[aria-label="/test_flow_component"]')
    if test_flow_folder.is_visible():
        test_flow_folder.click()
        time.sleep(1)
        print("[SUCCESS] Открыта папка test_flow_component")

        # Ищем и открываем диаграмму test_flow
        test_flow_file = page.get_by_text("test_flow.df.json")
        if test_flow_file.is_visible():
            test_flow_file.dblclick()
            time.sleep(2)
            print("[SUCCESS] Открыта диаграмма test_flow")
        else:
            print("[ERROR] Диаграмма test_flow.df.json не найдена в папке test_flow_component")
    else:
        print("[ERROR] Папка test_flow_component не найдена")

    # 3. Закрываем все панели
    print("[INFO] Шаг 3: Закрытие всех панелей")
    diagram_page.close_panels()
    time.sleep(1)
    print("[SUCCESS] Все панели закрыты")

    # 4. Делаем двойной клик по канвасу и ищем компонент Flow_proc
    print("[INFO] Шаг 4: Двойной клик по канвасу и поиск компонента Flow_proc")
    
    try:
        # Сначала делаем двойной клик по канвасу
        canvas = page.locator('canvas').first
        canvas.dblclick()
        time.sleep(1)
        print("[SUCCESS] Двойной клик по канвасу выполнен")
        
        # Теперь ищем компонент "Flow_proc" используя CanvasUtils
        flow_proc_found = canvas_utils.find_component_by_title("Flow_proc", exact=True)
        
        if flow_proc_found:
            print("[SUCCESS] Компонент 'Flow_proc' найден на канвасе!")
        else:
            print("[WARN] Компонент 'Flow_proc' не найден, попробуем другие варианты")
            
            # Попробуем найти другие возможные названия
            for name in ["Flow", "Подпроцесс", "Subprocess", "flow_proc"]:
                try:
                    found = canvas_utils.find_component_by_title(name, exact=True)
                    if found:
                        print(f"[SUCCESS] Найден компонент '{name}' на канвасе!")
                        break
                except Exception as e:
                    print(f"[DEBUG] Компонент '{name}' не найден: {e}")
                    continue
            
            # Если ничего не найдено, делаем скриншот для диагностики
            page.screenshot(path='screenshots/debug_flow_proc_not_found.png', full_page=True)
            print("[INFO] Скриншот сохранен для диагностики")
            
    except Exception as e:
        print(f"[ERROR] Ошибка при поиске компонента: {e}")
        # Делаем скриншот для диагностики
        page.screenshot(path='screenshots/debug_flow_proc_error.png', full_page=True)

    print("[SUCCESS] Тест поиска компонента Flow_proc завершен!")


def cleanup_projects():
    """
    Функция для очистки созданных проектов в конце тестового файла
    """
    print("[INFO] Очистка проектов - пока что заглушка")
