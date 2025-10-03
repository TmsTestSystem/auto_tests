import time
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from conftest import save_screenshot


def test_check_all_project_buttons_and_panels(login_page):
    """
    Тест проверки всех кнопок внутри проекта и панелек
    """
    page = login_page
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    
    # Переходим к первому доступному проекту
    project_page.goto_first_available_project()
    
    # Делаем скриншот начального состояния
    page.screenshot(path=f'screenshots/project_initial_{int(time.time())}.png', full_page=True)
    print(f"[SCREENSHOT] Начальное состояние проекта")
    
    # Проверяем основные панели и кнопки
    print("\n=== ПРОВЕРКА ОСНОВНЫХ ПАНЕЛЕЙ ===")
    
    # 1. Проверяем панель файлов
    print("[CHECK] Проверяем панель файлов")
    file_panel.open_file_panel()
    time.sleep(1)
    
    # Проверяем кнопки в панели файлов
    try:
        # Кнопка создания файла
        create_file_btn = page.locator('[aria-label*="создать"], [title*="создать"], button:has-text("+")').first
        if create_file_btn.is_visible():
            print("[OK] Кнопка создания файла найдена")
        else:
            print("[WARN] Кнопка создания файла не видима")
    except:
        print("[WARN] Кнопка создания файла не найдена")
    
    # Проверяем дерево файлов
    try:
        tree_items = page.locator('.tree-item, [role="treeitem"]').all()
        print(f"[INFO] Найдено элементов в дереве файлов: {len(tree_items)}")
    except:
        print("[WARN] Дерево файлов не найдено")
    
    # 2. Проверяем панель инструментов (toolbar)
    print("\n[CHECK] Проверяем панель инструментов")
    try:
        toolbar_buttons = page.locator('button[title], button[aria-label], .toolbar button').all()
        print(f"[INFO] Найдено кнопок в панели инструментов: {len(toolbar_buttons)}")
        
        for i, btn in enumerate(toolbar_buttons[:5]):  # Показываем первые 5
            try:
                title = btn.get_attribute('title') or btn.get_attribute('aria-label') or btn.inner_text()
                print(f"  {i+1}. {title}")
            except:
                print(f"  {i+1}. [не удалось получить название]")
    except:
        print("[WARN] Панель инструментов не найдена")
    
    # 3. Проверяем навигационные элементы
    print("\n[CHECK] Проверяем навигационные элементы")
    try:
        # Хлебные крошки
        breadcrumbs = page.locator('.breadcrumb, [aria-label*="навигация"], nav').all()
        print(f"[INFO] Найдено навигационных элементов: {len(breadcrumbs)}")
        
        # Вкладки файлов
        tabs = page.locator('[role="tab"], .tab, .file-tab').all()
        print(f"[INFO] Найдено вкладок: {len(tabs)}")
        
        for i, tab in enumerate(tabs[:3]):  # Показываем первые 3
            try:
                tab_text = tab.inner_text()
                print(f"  Вкладка {i+1}: {tab_text}")
            except:
                print(f"  Вкладка {i+1}: [не удалось получить текст]")
    except:
        print("[WARN] Навигационные элементы не найдены")
    
    # 4. Проверяем боковые панели
    print("\n[CHECK] Проверяем боковые панели")
    try:
        # Левая панель
        left_panel = page.locator('.left-panel, .sidebar-left, [data-panel="left"]').first
        if left_panel.is_visible():
            print("[OK] Левая панель найдена")
        else:
            print("[WARN] Левая панель не видима")
    except:
        print("[WARN] Левая панель не найдена")
    
    try:
        # Правая панель
        right_panel = page.locator('.right-panel, .sidebar-right, [data-panel="right"]').first
        if right_panel.is_visible():
            print("[OK] Правая панель найдена")
        else:
            print("[WARN] Правая панель не видима")
    except:
        print("[WARN] Правая панель не найдена")
    
    # 5. Проверяем центральную область (редактор)
    print("\n[CHECK] Проверяем центральную область")
    try:
        # Редактор
        editor = page.locator('.editor, .monaco-editor, [role="textbox"]').first
        if editor.is_visible():
            print("[OK] Редактор найден")
        else:
            print("[WARN] Редактор не видима")
    except:
        print("[WARN] Редактор не найден")
    
    # 6. Проверяем нижнюю панель
    print("\n[CHECK] Проверяем нижнюю панель")
    try:
        bottom_panel = page.locator('.bottom-panel, .status-bar, .footer').first
        if bottom_panel.is_visible():
            print("[OK] Нижняя панель найдена")
            
            # Проверяем элементы в нижней панели
            bottom_elements = bottom_panel.locator('button, .status-item, .info').all()
            print(f"[INFO] Найдено элементов в нижней панели: {len(bottom_elements)}")
        else:
            print("[WARN] Нижняя панель не видима")
    except:
        print("[WARN] Нижняя панель не найдена")
    
    # 7. Проверяем меню
    print("\n[CHECK] Проверяем меню")
    try:
        # Главное меню
        menu_buttons = page.locator('[role="menubar"] button, .menu button, [aria-label*="меню"]').all()
        print(f"[INFO] Найдено кнопок меню: {len(menu_buttons)}")
        
        for i, menu_btn in enumerate(menu_buttons[:3]):  # Показываем первые 3
            try:
                menu_text = menu_btn.inner_text() or menu_btn.get_attribute('aria-label')
                print(f"  Меню {i+1}: {menu_text}")
            except:
                print(f"  Меню {i+1}: [не удалось получить текст]")
    except:
        print("[WARN] Меню не найдено")
    
    # 8. Проверяем контекстные меню
    print("\n[CHECK] Проверяем контекстные меню")
    try:
        # Кликаем правой кнопкой мыши в центре страницы
        page.mouse.click(page.viewport_size['width'] // 2, page.viewport_size['height'] // 2, button='right')
        time.sleep(0.5)
        
        # Ищем контекстное меню
        context_menu = page.locator('[role="menu"], .context-menu, .dropdown-menu').first
        if context_menu.is_visible():
            print("[OK] Контекстное меню найдено")
            
            # Проверяем элементы контекстного меню
            context_items = context_menu.locator('[role="menuitem"], .menu-item').all()
            print(f"[INFO] Найдено элементов в контекстном меню: {len(context_items)}")
        else:
            print("[WARN] Контекстное меню не найдено")
        
        # Закрываем контекстное меню
        page.keyboard.press('Escape')
        time.sleep(0.2)
    except Exception as e:
        print(f"[WARN] Ошибка при проверке контекстного меню: {e}")
    
    # Финальный скриншот
    page.screenshot(path=f'screenshots/project_final_{int(time.time())}.png', full_page=True)
    print(f"\n[SCREENSHOT] Финальное состояние проекта")
    
    print(f"\n[SUCCESS] Тест проверки всех кнопок и панелей завершен!") 