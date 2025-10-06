"""
Тест для компонента Query
"""
import time
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from pages.db_connector_page import DBConnectorPage
from pages.diagram_page import DiagramPage
from conftest import save_screenshot


def test_flow_query(login_page, shared_flow_project):
    """
    Тест для работы с компонентом Query
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    diagram_page = DiagramPage(page)

    print(f"[INFO] Запуск теста Query в проекте: {project_code}")

    assert project_page.goto_project(project_code), f"Переход в проект {project_code} не удался!"
    time.sleep(2)

    file_panel = FilePanelPage(page)
    data_struct = DataStructPage(page)

    try:
        is_open = page.get_by_label("board_toolbar_panel").is_visible()
    except Exception:
        is_open = False
    if not is_open:
        file_panel.open_file_panel()
        time.sleep(0.5)
    print("[INFO] Файловая панель открыта")

    # 1. Создаем файл базы данных 'db_query' в папке 'db_connection'
    print("[INFO] Шаг 1: Создание файла базы данных 'db_query' в папке 'db_connection'")

    db_connection_folder = page.locator('[aria-label="treeitem_label"]:has-text("db_connection")')
    assert db_connection_folder.count() > 0, "Папка 'db_connection' не найдена в файловой панели!"
    print("[INFO] Папка 'db_connection' найдена")
    
    db_connection_folder.first.click(button="right")
    time.sleep(1)
    print("[INFO] Правый клик по папке 'db_connection' выполнен")

    create_menu = page.get_by_text("Создать", exact=True)
    assert create_menu.is_visible(), "Меню 'Создать' не найдено в контекстном меню!"
    create_menu.click()
    time.sleep(0.5)
    print("[INFO] Клик по меню 'Создать' в контекстном меню")

    time.sleep(2)
    
    db_menu = page.locator('[aria-label="database_connection_info"]')
    assert db_menu.count() > 0, "Меню 'Подключение к БД' не найдено в подменю!"
    db_menu.click()
    time.sleep(1)
    print("[INFO] Клик по меню 'Подключение к БД' в подменю")

    timestamp = int(time.time())
    db_file_name = f"db_query_{timestamp}"
    name_input = page.get_by_role("textbox", name="treeitem_label_field")
    name_input.wait_for(state="visible", timeout=10000)
    assert name_input.is_visible(), "Поле ввода названия не появилось!"
    name_input.fill(db_file_name)
    name_input.press("Enter")
    time.sleep(2)
    print(f"[INFO] Создан файл базы данных '{db_file_name}'")

    # 2. Настраиваем подключение к базе данных
    print("[INFO] Шаг 2: Настройка подключения к базе данных")

    db_file_item = page.locator(f'[aria-label="treeitem_label"]:has-text("{db_file_name}")')
    assert db_file_item.is_visible(), f"Файл базы данных '{db_file_name}' не найден!"
    db_file_item.dblclick()
    time.sleep(2)
    print(f"[INFO] Открыт файл базы данных '{db_file_name}'")

    submit_button = page.get_by_role("button", name="dbconnection_submit")
    submit_button.wait_for(state="visible", timeout=10000)
    print("[INFO] Страница настройки БД загружена")

    db_connector = DBConnectorPage(page)
    
    db_connector.configure_and_save_connection()
    print("[INFO] Подключение к базе данных настроено и сохранено")

    print("[INFO] Шаг 3: Открытие диаграммы 'test_query.df.json' в папке 'test_flow_component'")

    test_flow_folder = page.locator('[aria-label="treeitem_label"]:has-text("test_flow_component")')
    assert test_flow_folder.count() > 0, "Папка 'test_flow_component' не найдена в файловой панели!"
    print("[INFO] Папка 'test_flow_component' найдена")
    test_flow_folder.click()
    time.sleep(1)
    print("[INFO] Клик по папке 'test_flow_component' выполнен")

    test_query_file = page.locator('[aria-label="treeitem_label"]:has-text("test_query.df.json")')
    assert test_query_file.count() > 0, "Файл 'test_query.df.json' не найден в папке!"
    print("[INFO] Файл 'test_query.df.json' найден")
    test_query_file.dblclick()
    time.sleep(2)
    print("[INFO] Диаграмма 'test_query.df.json' открыта")

    canvas = page.locator('canvas').first
    canvas.wait_for(state="visible", timeout=10000)
    time.sleep(2)
    print("[INFO] Canvas диаграммы загружен")

    try:
        if page.get_by_label("board_toolbar_panel").is_visible():
            file_manager_btn = page.get_by_role("button", name="board_toolbar_filemanager_button")
            if file_manager_btn.is_visible():
                file_manager_btn.click()
                time.sleep(0.5)
                print("[INFO] Файловая панель закрыта")
    except Exception as e:
        print(f"[INFO] Файловая панель уже закрыта или не найдена: {e}")

    try:
        details_panel = page.locator('[aria-label="diagram_details_panel"]')
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт или не найден: {e}")

    print("[INFO] Шаг 4: Поиск и настройка компонента Query на канвасе")

    canvas_utils = CanvasUtils(page)
    query_found = canvas_utils.find_component_by_title("Query", timeout=10000)
    assert query_found, "Компонент 'Query' не найден на канвасе!"
    print("[INFO] Компонент 'Query' найден и двойной клик выполнен")

    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт")

    print("[INFO] Шаг 5: Настройка подключения к БД в компоненте Query")

    select_file_button = page.get_by_role("button", name="textfield_select_file_button")
    assert select_file_button.is_visible(), "Кнопка выбора файла не найдена!"
    select_file_button.click()
    time.sleep(1)
    print("[INFO] Клик по кнопке выбора файла выполнен")

    modal = page.locator('.decision-flow__Modal_open___NIla4.src__FileManagerModal___HeqlP')
    modal.wait_for(state="visible", timeout=10000)
    print("[INFO] Модалка выбора БД открыта")

    db_file_name_with_extension = f"{db_file_name}.db.json"
    db_file_item = page.get_by_role("treeitem", name=f"/{db_file_name_with_extension}")
    
    if db_file_item.count() == 0:
        db_file_item = page.get_by_role("treeitem").filter(has_text=db_file_name)
    
    assert db_file_item.count() > 0, f"Файл подключения '{db_file_name}' не найден в модалке!"
    print(f"[INFO] Найден файл подключения: {db_file_name}")
    
    db_file_item.locator("div").nth(1).click()
    time.sleep(1)
    print("[INFO] Клик по файлу подключения выполнен")

    select_button = page.get_by_role("button", name="filemanager_select_button")
    assert select_button.count() > 0, "Кнопка 'Выбрать' не найдена в модалке!"
    select_button.click()
    time.sleep(1)
    print("[INFO] Клик по кнопке 'Выбрать' выполнен")

    modal.wait_for(state="hidden", timeout=10000)
    print("[INFO] Модалка выбора БД закрыта")

    print("[INFO] Шаг 6: Заполнение SQL запроса в поле редактора")

    sql_editor = page.get_by_role("textbox", name="editor_view").first
    assert sql_editor.is_visible(), "Поле редактора SQL не найдено!"
    print("[INFO] Поле редактора SQL найдено")

    sql_query = f"SELECT * FROM projects WHERE code = '{project_code}'"
    sql_editor.fill(sql_query)
    time.sleep(1)
    print(f"[INFO] SQL запрос введен: {sql_query}")

    try:
        details_panel = page.locator('[aria-label="diagram_details_panel"]')
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт или не найден: {e}")

    print("[INFO] Шаг 7: Настройка компонента Output")

    output_found = canvas_utils.find_component_by_title("Output", timeout=10000)
    assert output_found, "Компонент 'Output' не найден на канвасе!"
    print("[INFO] Компонент 'Output' найден и двойной клик выполнен")

    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт")

    data_field = page.get_by_role("textbox", name="data")
    if data_field.count() == 0:
        data_field = page.locator('input[name="data"], textarea[name="data"]')
    
    assert data_field.count() > 0, "Поле 'Данные' не найдено!"
    data_field.fill("$node.Query.data[0]")
    time.sleep(1)
    print("[INFO] Поле 'Данные' заполнено: $node.Query.data[0]")

    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Output")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    print("[INFO] Шаг 8: Запуск диаграммы")

    success = diagram_page.run_diagram_and_wait(completion_timeout=15000)
    
    assert success, "Диаграмма не выполнилась успешно!"
    print("[INFO] Диаграмма завершилась успешно!")

    print("[INFO] Шаг 9: Проверка JSON данных в модальном окне")

    canvas = page.locator('canvas').first
    canvas.dblclick()
    time.sleep(1)
    print("[INFO] Двойной клик по канвасу выполнен")

    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Сайдбар открыт")

    process_tab = page.get_by_text("Процесс", exact=True)
    assert process_tab.is_visible(), "Вкладка 'Процесс' не найдена!"
    process_tab.click()
    time.sleep(1)
    print("[INFO] Переход на вкладку 'Процесс' выполнен")

    analysis_tab = page.get_by_text("Анализ", exact=True)
    assert analysis_tab.is_visible(), "Подвкладка 'Анализ' не найдена!"
    analysis_tab.click()
    time.sleep(1)
    print("[INFO] Переход на подвкладку 'Анализ' выполнен")

    full_view_button = page.get_by_role("button", name="formitem_full_view_button").nth(1)
    assert full_view_button.is_visible(), "Кнопка 'formitem_full_view_button' не найдена!"
    full_view_button.click()
    time.sleep(1)
    print("[INFO] Кнопка 'formitem_full_view_button' нажата")

    json_modal = page.locator('[role="dialog"]:has-text("Просмотр JSON")')
    json_modal.wait_for(state="visible", timeout=10000)
    print("[INFO] Модальное окно 'Просмотр JSON' открыто")
    
    save_screenshot(page, f"json_modal_{project_code}")
    
    time.sleep(3)

    json_text = ""
    
    view_lines = page.locator('[role="dialog"] .view-lines')
    assert view_lines.count() > 0, "Monaco Editor не найден в модальном окне!"
    
    json_text = view_lines.inner_text()
    print(f"[INFO] JSON данные получены из Monaco Editor (длина: {len(json_text)}): {json_text[:300]}...")
    
    assert json_text.strip(), "JSON данные не найдены в Monaco Editor!"

    import re
    json_text_clean = re.sub(r'[\xa0\u00a0]', ' ', json_text)  # Заменяем non-breaking spaces на обычные пробелы
    json_text_clean = json_text_clean.strip()
    print(f"[INFO] Очищенный JSON (длина: {len(json_text_clean)}): {json_text_clean[:200]}...")

    import json
    try:
        json_data = json.loads(json_text_clean)
        print("[INFO] JSON успешно распарсен")
        
        assert "data" in json_data, "Поле 'data' не найдено в JSON"
        assert "error" in json_data, "Поле 'error' не найдено в JSON"
        
        data = json_data["data"]
        
        assert data["code"] == project_code, f"Код проекта не совпадает: ожидался '{project_code}', получен '{data['code']}'"
        assert data["default_branch"] == "main", f"Ветка по умолчанию не 'main': {data['default_branch']}"
        assert data["deleted_at"] is None, f"Проект удален: {data['deleted_at']}"
        assert "id" in data, "Поле 'id' не найдено в данных проекта"
        assert isinstance(data["id"], int), "Поле 'id' должно быть числом"
        
        print("[INFO] Все проверки JSON данных пройдены успешно!")
        print(f"[INFO] Код проекта: {data['code']}")
        print(f"[INFO] ID проекта: {data['id']}")
        print(f"[INFO] Ветка по умолчанию: {data['default_branch']}")
        
    except json.JSONDecodeError as e:
        raise Exception(f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        raise Exception(f"Ошибка проверки JSON данных: {e}")

    close_button = page.locator('[role="dialog"] button[aria-label="close"], [role="dialog"] .close-button')
    if close_button.count() > 0:
        close_button.first.click()
        time.sleep(1)
        print("[INFO] Модальное окно закрыто")

    save_screenshot(page, f"query_test_complete_{project_code}")

    print("[SUCCESS] Все шаги теста Query выполнены успешно!")
