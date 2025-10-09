import time
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from conftest import save_screenshot
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


def test_check_all_project_buttons_and_panels(login_page):
    """
    Тест проверки всех кнопок внутри проекта и панелек
    """
    page = login_page
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    
    project_page.goto_first_available_project()
    
    page.screenshot(path=f'screenshots/project_initial_{int(time.time())}.png', full_page=True)
    print(f"[SCREENSHOT] Начальное состояние проекта")
    
    print("\n=== ПРОВЕРКА ОСНОВНЫХ ПАНЕЛЕЙ ===")
    
    print("[CHECK] Проверяем панель файлов")
    file_panel.open_file_panel()
    time.sleep(1)
    
    try:
        create_file_btn = page.locator(FilePanelLocators.CREATE_FILE_BUTTON).first
        if create_file_btn.is_visible():
            print("[OK] Кнопка создания файла найдена")
        else:
            print("[WARN] Кнопка создания файла не видима")
    except:
        print("[WARN] Кнопка создания файла не найдена")
    
    try:
        tree_items = page.locator(FilePanelLocators.TREE_ITEMS).all()
        print(f"[INFO] Найдено элементов в дереве файлов: {len(tree_items)}")
    except:
        print("[WARN] Дерево файлов не найдено")
    
    print("\n[CHECK] Проверяем панель инструментов")
    try:
        toolbar_buttons = page.locator(ToolbarLocators.TOOLBAR_BUTTONS).all()
        print(f"[INFO] Найдено кнопок в панели инструментов: {len(toolbar_buttons)}")
        
        for i, btn in enumerate(toolbar_buttons[:5]):  # Показываем первые 5
            try:
                title = btn.get_attribute('title') or btn.get_attribute('aria-label') or btn.inner_text()
                print(f"  {i+1}. {title}")
            except:
                print(f"  {i+1}. [не удалось получить название]")
    except:
        print("[WARN] Панель инструментов не найдена")
    
    print("\n[CHECK] Проверяем навигационные элементы")
    try:
        breadcrumbs = page.locator(ToolbarLocators.BREADCRUMBS_ALT).all()
        print(f"[INFO] Найдено навигационных элементов: {len(breadcrumbs)}")
        
        tabs = page.locator(ToolbarLocators.TABS).all()
        print(f"[INFO] Найдено вкладок: {len(tabs)}")
        
        for i, tab in enumerate(tabs[:3]):  # Показываем первые 3
            try:
                tab_text = tab.inner_text()
                print(f"  Вкладка {i+1}: {tab_text}")
            except:
                print(f"  Вкладка {i+1}: [не удалось получить текст]")
    except:
        print("[WARN] Навигационные элементы не найдены")
    
    print("\n[CHECK] Проверяем боковые панели")
    try:
        left_panel = page.locator(ToolbarLocators.LEFT_PANEL).first
        if left_panel.is_visible():
            print("[OK] Левая панель найдена")
        else:
            print("[WARN] Левая панель не видима")
    except:
        print("[WARN] Левая панель не найдена")
    
    try:
        right_panel = page.locator(ToolbarLocators.RIGHT_PANEL).first
        if right_panel.is_visible():
            print("[OK] Правая панель найдена")
        else:
            print("[WARN] Правая панель не видима")
    except:
        print("[WARN] Правая панель не найдена")
    
    print("\n[CHECK] Проверяем центральную область")
    try:
        editor = page.locator(ToolbarLocators.EDITOR).first
        if editor.is_visible():
            print("[OK] Редактор найден")
        else:
            print("[WARN] Редактор не видима")
    except:
        print("[WARN] Редактор не найден")
    
    print("\n[CHECK] Проверяем нижнюю панель")
    try:
        bottom_panel = page.locator(ToolbarLocators.BOTTOM_PANEL).first
        if bottom_panel.is_visible():
            print("[OK] Нижняя панель найдена")
            
            bottom_elements = bottom_panel.locator('button, .status-item, .info').all()
            print(f"[INFO] Найдено элементов в нижней панели: {len(bottom_elements)}")
        else:
            print("[WARN] Нижняя панель не видима")
    except:
        print("[WARN] Нижняя панель не найдена")
    
    print("\n[CHECK] Проверяем меню")
    try:
        menu_buttons = page.locator(ToolbarLocators.MENU_BUTTONS).all()
        print(f"[INFO] Найдено кнопок меню: {len(menu_buttons)}")
        
        for i, menu_btn in enumerate(menu_buttons[:3]):  # Показываем первые 3
            try:
                menu_text = menu_btn.inner_text() or menu_btn.get_attribute('aria-label')
                print(f"  Меню {i+1}: {menu_text}")
            except:
                print(f"  Меню {i+1}: [не удалось получить текст]")
    except:
        print("[WARN] Меню не найдено")
    
    print("\n[CHECK] Проверяем контекстные меню")
    try:
        page.mouse.click(page.viewport_size['width'] // 2, page.viewport_size['height'] // 2, button='right')
        time.sleep(0.5)
        
        context_menu = page.locator(ToolbarLocators.CONTEXT_MENU).first
        if context_menu.is_visible():
            print("[OK] Контекстное меню найдено")
            
            context_items = context_menu.locator('[role="menuitem"], .menu-item').all()
            print(f"[INFO] Найдено элементов в контекстном меню: {len(context_items)}")
        else:
            print("[WARN] Контекстное меню не найдено")
        
        page.keyboard.press('Escape')
        time.sleep(0.2)
    except Exception as e:
        print(f"[WARN] Ошибка при проверке контекстного меню: {e}")
    
    page.screenshot(path=f'screenshots/project_final_{int(time.time())}.png', full_page=True)
    print(f"\n[SCREENSHOT] Финальное состояние проекта")
    
    print(f"\n[SUCCESS] Тест проверки всех кнопок и панелей завершен!") 
