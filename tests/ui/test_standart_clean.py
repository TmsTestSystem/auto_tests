import time
import os
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from conftest import save_screenshot, get_project_by_code, delete_project_by_id


def test_flow_standart(login_page, shared_flow_project):
    """
    Тест для поиска и клика по компонентам диаграммы через заголовки
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    
    # 1. Переход к нужному проекту по коду (проект уже создан фикстурой)
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)

    # 2. Открываем левый сайдбар (filemanager)
    page.get_by_role("button", name="board_toolbar_filemanager_button").click()
    time.sleep(1)

    # 3. В сайдбаре раскрываем папку
    folder = page.locator('[aria-label="/test_flow_component"]')
    folder.wait_for(state="visible", timeout=15000)
    folder.click()
    time.sleep(1)

    # 4. Открываем файл
    board_panel = page.get_by_label("board_toolbar_panel")
    file_item = board_panel.get_by_text("test_standart.df.json")
    file_item.wait_for(state="visible", timeout=10000)
    file_item.dblclick()
    time.sleep(2)

    # 5. Создаём структуру данных в папке shema
    file_panel = FilePanelPage(page)
    data_struct = DataStructPage(page)
    
    try:
        is_open = False
        try:
            is_open = page.get_by_label("board_toolbar_panel").is_visible()
        except Exception:
            is_open = False
        if not is_open:
            file_panel.open_file_panel()
            time.sleep(0.5)
    except Exception:
        pass
    
    shema_folder = page.locator('[aria-label="treeitem_label"]:has-text("shema")')
    assert shema_folder.count() > 0, "Папка 'shema' не найдена в проекте!"
    print("[INFO] Папка 'shema' найдена")
    shema_folder.first.click(button="right")
    time.sleep(1)
    print("[INFO] Правый клик по папке 'shema' выполнен")

    create_menu = page.get_by_text("Создать", exact=True)
    assert create_menu.is_visible(), "Пункт 'Создать' не найден в контекстном меню!"
    create_menu.click()
    time.sleep(0.5)
    print("[INFO] Выбран пункт 'Создать' из контекстного меню")
    
    data_structures_menu = page.get_by_text("Структуры данных", exact=True)
    assert data_structures_menu.is_visible(), "Пункт 'Структуры данных' не найден в подменю!"
    data_structures_menu.click()
    time.sleep(1)
    print("[INFO] Выбран пункт 'Структуры данных' из подменю")
    
    name_input = page.get_by_role("textbox", name="treeitem_label_field")
    name_input.wait_for(state="visible", timeout=10000)
    assert name_input.is_visible(), "Поле ввода имени не появилось!"
    
    timestamp = int(time.time())
    data_struct_name = f"datastruct_{timestamp}"
    name_input.fill(data_struct_name)
    page.keyboard.press("Enter")
    time.sleep(1)
    print(f"[INFO] Создан файл структуры данных: {data_struct_name}")

    try:
        file_panel.open_file_panel()
        possible = page.locator('[aria-label="treeitem_label"]').filter(has_text=data_struct_name)
        if possible.count():
            possible.first.hover()
    except Exception:
        pass
    time.sleep(1)
    
    # Кликаем по созданной структуре данных чтобы открыть её для редактирования
    data_struct_item = page.locator('[aria-label="treeitem_label"]').filter(has_text=data_struct_name)
    if data_struct_item.count() > 0:
        data_struct_item.first.click()
        time.sleep(1)
        print(f"[INFO] Клик по структуре данных '{data_struct_name}' выполнен")
    
    schema_name = f"test_schema_{int(time.time())}"
    data_struct.create_schema(schema_name)

    # Открываем панель деталей диаграммы если она закрыта
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    if not details_panel.is_visible():
        switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if switcher.is_visible():
            switcher.click()
            time.sleep(0.3)
            print("[INFO] Панель деталей диаграммы открыта")

    page.wait_for_selector('button[aria-label="datastructureeditor_create_attribute_button"]', timeout=10000)
    time.sleep(0.5)
    
    attributes = [
        {"name": "test_string", "type": "string", "desc": "Тестовая строка"},
        {"name": "test_number", "type": "integer", "desc": "Тестовое число"},
        {"name": "test_bool", "type": "boolean", "desc": "Тестовый флаг"}
    ]
    
    for idx, attr in enumerate(attributes):
        # Переключаемся на вкладку структуры данных перед созданием атрибута
        try:
            structure_tab = page.get_by_text("Структуры данных", exact=True)
            if structure_tab.is_visible():
                structure_tab.click()
                time.sleep(0.5)
                print(f"[INFO] Переключились на вкладку 'Структуры данных' для создания атрибута {idx+1}")
        except Exception as e:
            print(f"[WARN] Не удалось переключиться на вкладку 'Структуры данных': {e}")
        
        data_struct.click_create_attribute_button()
        page.wait_for_selector(f'input[name="attributes.{idx}.name"]', timeout=10000)
        time.sleep(0.5)
        data_struct.fill_attribute_name_by_index(idx, attr["name"])
        data_struct.press_enter_attribute_name_by_index(idx)
        time.sleep(0.5)
        if attr["type"] != "string" or idx > 0:
            data_struct.select_attribute_type_by_index(idx, attr["type"])
            time.sleep(0.5)
        data_struct.fill_attribute_description_by_index(idx, attr["desc"])
        time.sleep(0.5)
        
        print(f"[SUCCESS] Создан атрибут {idx+1}: {attr['name']} ({attr['type']})")
        
        try:
            page.keyboard.press("Control+S")
            time.sleep(1)
        except Exception:
            pass
    
    print(f"[SUCCESS] Создана схема '{schema_name}' с {len(attributes)} атрибутами")
    
    try:
        test_standart_tab = page.locator('[aria-label*="test_standart"], [data-tooltip*="test_standart"]').first
        if test_standart_tab.is_visible():
            test_standart_tab.click()
            time.sleep(1)
            print("[INFO] Возврат на вкладку 'test_standart' выполнен")
        else:
            try:
                board_panel = page.get_by_label("board_toolbar_panel")
                standart_file = board_panel.get_by_text("test_standart.df.json").first
                standart_file.click()
                time.sleep(1)
                print("[INFO] Возврат на вкладку 'test_standart' выполнен (через панель)")
            except Exception:
                print("[WARN] Не удалось найти вкладку test_standart, продолжаем")
    except Exception as e:
        print(f"[WARN] Ошибка при возврате на вкладку 'test_standart': {e}")
        
        try:
            canvas = page.locator('canvas').first
            canvas.wait_for(state="visible", timeout=10000)
            time.sleep(2)
            print("[INFO] Диаграмма test_standart загружена")
        except Exception:
            print("[WARN] Диаграмма может быть не загружена")

    # 6. Кликаем по компоненту Input на canvas и открываем правый сайдбар
    print("[INFO] Шаг 6: Поиск и клик по компоненту Input")
    
    canvas_utils = CanvasUtils(page)
    
    # Используем новую утилиту для поиска компонента Input
    if not canvas_utils.find_component_by_title("Input", exact=True):
        print("[WARN] Не удалось найти компонент Input через точный поиск, пробуем альтернативные методы")
        # Пробуем через координаты как fallback
        if not canvas_utils.find_component_by_position(0.45, 0.55):
            raise Exception("Не удалось найти или кликнуть по компоненту Input")

    # Выбираем созданную структуру данных и схему
    print("[INFO] Выбор созданной структуры данных и схемы")
    
    if not canvas_utils.select_structure_data(data_struct_name, schema_name):
        save_screenshot(page, f"structure_selection_error_{project_code}")
        raise Exception(f"Не удалось выбрать структуру данных '{data_struct_name}' или схему '{schema_name}'")

    # Настраиваем процесс и анализ
    try:
        page.get_by_text("Процесс", exact=True).click()
        time.sleep(0.3)
        page.get_by_text("Анализ", exact=True).click()
        time.sleep(0.3)
        page.locator('xpath=/html/body/div[1]/div[2]/div[1]/div[5]/div/div[3]/div[3]/div[2]/div[3]/div/div[1]/div/div[2]/div[1]/button[1]').click()
        time.sleep(2)  # Пауза после предзаполнения
        
        try:
            view_lines_text = page.locator(".view-lines").first.text_content()
            print(f"Текст из .view-lines: {view_lines_text}")
        except Exception as e:
            print(f"Не удалось получить текст из .view-lines: {e}")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке процесса и анализа: {e}")
    
    # 7. Кликаем по компоненту Output на canvas
    print("[INFO] Шаг 7: Поиск и клик по компоненту Output")
    
    if not canvas_utils.find_component_by_title("Output", exact=True):
        print("[WARN] Не удалось найти компонент Output через точный поиск, пробуем альтернативные методы")
        # Пробуем через координаты как fallback
        if not canvas_utils.find_component_by_position(0.7, 0.7):
            raise Exception("Не удалось найти или кликнуть по компоненту Output")
    
    time.sleep(1)
    
    try:
        page.get_by_text("Компонент", exact=True).click()
        time.sleep(0.5)
        print("Переключились на вкладку Компонент")
    except Exception as e:
        print(f"Не удалось переключиться на вкладку Компонент: {e}")
    
    try:
        page.get_by_text("Параметры", exact=True).click()
        time.sleep(0.5)
        print("Переключились на подвкладку Параметры")
    except Exception as e:
        print(f"Не удалось переключиться на подвкладку Параметры: {e}")
                
    try:
        data_field = page.get_by_role("textbox", name="inputs_config.data.value")
        data_field.fill("$node.Input.data")
        time.sleep(0.5)
    except Exception as e:
        print(f"Не удалось заполнить поле данных: {e}")
    
    play_btn = page.get_by_role("button", name="diagram_play_button")
    play_btn.wait_for(state="visible", timeout=5000)
    play_btn.click()
    time.sleep(2)  # Ждём запуска диаграммы
    
    try:
        toast = page.locator('.Toast__Toast___ZqZzU[aria-label="toast"]')
        toast.wait_for(state="visible", timeout=15000)  # Ждём до 15 секунд появления тоста
        print("[INFO] Тост о завершении диаграммы появился")
        
        toast_title = toast.locator('.Toast__Title___-0bIZ')
        assert toast_title.is_visible(), "Заголовок тоста не найден!"
        title_text = toast_title.text_content()
        assert "Диаграмма завершена" in title_text, f"Неожиданный заголовок тоста: {title_text}"
        print(f"[SUCCESS] Заголовок тоста: {title_text}")
        
        toast_description = toast.locator('.Toast__Description___YwLXR')
        assert toast_description.is_visible(), "Описание тоста не найдено!"
        description_text = toast_description.text_content()
        assert "Диаграмма завершена на компоненте \"Output\"" in description_text, f"Неожиданное описание тоста: {description_text}"
        print(f"[SUCCESS] Описание тоста: {description_text}")
        
    except Exception as e:
        print(f"[ERROR] Не удалось найти или проверить тост о завершении диаграммы: {e}")
        page.screenshot(path=f'screenshots/toast_error_{int(time.time())}.png', full_page=True)
        raise
    
    try:
        page.get_by_text("Анализ", exact=True).click()
        time.sleep(0.5)
        print("Переключились на Анализ для Output")
    except Exception as e:
        print(f"Не удалось переключиться на Анализ: {e}")
    
    try:
        data_field = page.get_by_text("Data").first
        data_content = data_field.text_content()
        print(f"Содержимое поля Data (по тексту): {data_content}")
    except Exception:
        try:
            data_field = page.locator('xpath=//div[contains(text(), "test_string") or contains(text(), "test_number") or contains(text(), "test_bool")]').first
            data_content = data_field.text_content()
            print(f"Содержимое поля Data (по XPath): {data_content}")
        except Exception:
            try:
                data_field = page.locator('[class*="data"], [data-testid*="data"], textarea, pre, code').first
                data_content = data_field.text_content()
                print(f"Содержимое поля Data (по селектору): {data_content}")
            except Exception as e:
                print(f"Не удалось найти поле Data: {e}")
                data_content = ""
        
        if data_content:
            expected_data = '{"test_string":"","test_number":0,"test_bool":false}'
            if expected_data in data_content or data_content in expected_data:
                print("SUCCESS: Данные в поле Data соответствуют предзаполненным!")
            else:
                print(f"ERROR: Данные не совпадают. Ожидали: {expected_data}, получили: {data_content}")
        else:
            print("ERROR: Поле Data не найдено или пустое")

    # 7. Финальный скриншот
    save_screenshot(page, f"component_search_complete_{project_code}")
    time.sleep(10)


def cleanup_projects():
    """
    Функция для очистки созданных проектов в конце тестового файла
    """
    # TODO: Реализовать очистку всех созданных проектов
    print("[INFO] Очистка проектов - пока что заглушка")
