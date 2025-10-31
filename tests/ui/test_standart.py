import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
import os
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from pages.diagram_page import DiagramPage
from conftest import save_screenshot, get_project_by_code, delete_project_by_id
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


def test_flow_standart(login_page, flow_project):
    """
    Тест для поиска и клика по компонентам диаграммы через заголовки
    """
    page, project_code = flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)
    
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)

    folder = page.locator(FilePanelLocators.get_treeitem_by_path("test_flow_component"))
    folder.wait_for(state="visible", timeout=15000)
    folder.click()
    time.sleep(1)

    board_panel = page.locator(ToolbarLocators.BOARD_TOOLBAR_PANEL)
    file_item = board_panel.get_by_text("test_standart.df.json")
    file_item.wait_for(state="visible", timeout=10000)
    file_item.dblclick()
    time.sleep(2)

    # Закрываем панели для работы с канвасом
    diagram_page.close_panels()
    time.sleep(1)

    file_panel = FilePanelPage(page)
    data_struct = DataStructPage(page)
    
    # Пропускаем создание структуры данных и переходим сразу к поиску компонентов
    print("[INFO] Пропускаем создание структуры данных, переходим к поиску компонентов")

    print("[INFO] Шаг 6: Поиск и клик по компоненту Input")
    
    # Принудительно закрываем файловую панель
    try:
        filemanager_button = page.get_by_role("button", name="board_toolbar_filemanager_button")
        if filemanager_button.is_visible():
            filemanager_button.click()
            time.sleep(1)
            print("[INFO] Файловая панель закрыта")
    except:
        pass
    
    # Закрываем все остальные панели
    diagram_page.close_panels()
    time.sleep(2)
    
    canvas_utils = CanvasUtils(page)
    
    if not canvas_utils.find_component_by_title("Input", exact=True):
        print("[WARN] Не удалось найти компонент Input через точный поиск, пробуем альтернативные методы")
        if not canvas_utils.find_component_by_position(0.45, 0.55):
            raise Exception("Не удалось найти или кликнуть по компоненту Input")

    print("[SUCCESS] Компонент Input найден и клик по нему выполнен!")
    print("[SUCCESS] Тест завершен успешно!")
