"""
Тест для компонента Query
"""
import base64
import json
import re
import time
from api.file_panel_api import FilePanelAPI
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from pages.db_connector_page import DBConnectorPage
from pages.diagram_page import DiagramPage
from conftest import save_screenshot, wait_for_canvas_with_refresh
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


def _current_branch(page) -> str:
    match = re.search(r"/branch/([^/?#]+)", page.url)
    return match.group(1) if match else "main"


def _patch_query_diagram_via_api(
    project_code: str,
    branch: str,
    process_path: str,
    db_path: str,
    sql_query: str,
    output_value: str,
) -> None:
    api = FilePanelAPI(project_code, branch=branch)
    diagram = json.loads(api.get_file_content(process_path))
    output_patched = False
    for component in diagram.get("components", []):
        if component.get("title") == "Output":
            component.setdefault("inputs_config", {}).setdefault("data", {})["value"] = output_value
            output_patched = True
        elif component.get("title") == "Query":
            component.setdefault("config", {}).update(
                {
                    "db_connection_path": db_path,
                    "query": sql_query,
                    "sql_statement": sql_query,
                    "timeout": 60,
                }
            )
    if not output_patched:
        raise AssertionError(f"Компонент Output не найден в {process_path}")
    content = json.dumps(diagram, ensure_ascii=False, indent=2).encode("utf-8")
    api.import_file(process_path, base64.b64encode(content).decode("ascii"))
    print(f"[INFO] Query и Output.data обновлены через API: {output_value}")


def test_flow_query(login_page, flow_project):
    """
    Тест для работы с компонентом Query
    """
    page, project_code = flow_project
    project_page = ProjectPage(page)
    diagram_page = DiagramPage(page)

    print(f"[INFO] Запуск теста Query в проекте: {project_code}")

    assert project_page.goto_project(project_code), f"Переход в проект {project_code} не удался!"
    time.sleep(2)

    file_panel = FilePanelPage(page)
    data_struct = DataStructPage(page)

    is_open = page.locator(ToolbarLocators.BOARD_TOOLBAR_PANEL).is_visible()
    if not is_open:
        file_panel.open_file_panel()
        time.sleep(0.5)
    print("[INFO] Файловая панель открыта")

    print("[INFO] Шаг 1: Создание файла базы данных 'db_query' в папке 'db_connection'")

    db_connection_folder = page.locator(FilePanelLocators.get_treeitem_by_name("db_connection"))
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
    
    db_menu = page.locator(FilePanelLocators.DATABASE_CONNECTION_INFO)
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

    print("[INFO] Шаг 2: Настройка подключения к базе данных")

    db_file_item = page.locator(FilePanelLocators.get_treeitem_by_name(db_file_name))
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

    test_flow_folder = page.locator(FilePanelLocators.get_treeitem_by_name("test_flow_component"))
    assert test_flow_folder.count() > 0, "Папка 'test_flow_component' не найдена в файловой панели!"
    print("[INFO] Папка 'test_flow_component' найдена")
    test_flow_folder.click()
    time.sleep(1)
    print("[INFO] Клик по папке 'test_flow_component' выполнен")

    test_query_file = page.locator(FilePanelLocators.get_treeitem_by_name("test_query.df.json"))
    assert test_query_file.count() > 0, "Файл 'test_query.df.json' не найден в папке!"
    print("[INFO] Файл 'test_query.df.json' найден")
    test_query_file.dblclick()
    time.sleep(2)
    print("[INFO] Диаграмма 'test_query.df.json' открыта")

    # Ждем загрузки canvas с рефрешем при таймауте
    assert wait_for_canvas_with_refresh(page, timeout=10000, max_refreshes=1), "Canvas не загрузился даже после рефреша!"
    canvas = page.locator(CanvasLocators.CANVAS).first
    time.sleep(1)
    print("[INFO] Canvas диаграммы загружен")

    if page.get_by_label("board_toolbar_panel").is_visible():
        file_manager_btn = page.get_by_role("button", name="board_toolbar_filemanager_button")
        if file_manager_btn.is_visible():
            file_manager_btn.click()
            time.sleep(0.5)
            print("[INFO] Файловая панель закрыта")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    if details_panel.is_visible():
        switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if switcher.is_visible():
            switcher.click()
            time.sleep(0.5)
            print("[INFO] Правый сайдбар закрыт")

    print("[INFO] Шаг 4: Поиск и настройка компонента Query на канвасе")

    canvas_utils = CanvasUtils(page)
    query_found = canvas_utils.find_component_by_title("Query", timeout=10000)
    assert query_found, "Компонент 'Query' не найден на канвасе!"
    print("[INFO] Компонент 'Query' найден и двойной клик выполнен")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт")

    print("[INFO] Шаг 5: Настройка подключения к БД в компоненте Query")

    select_file_button = page.get_by_role("button", name="textfield_select_file_button")
    select_file_button.wait_for(state="visible", timeout=15000)
    assert select_file_button.is_visible(), "Кнопка выбора файла не найдена!"
    select_file_button.click()
    time.sleep(1)
    print("[INFO] Клик по кнопке выбора файла выполнен")

    # В текущем UI нет стабильного test-id на модалке, поэтому ищем файл по treeitem-имени
    db_file_name_with_extension = f"{db_file_name}.db.json"
    db_file_item = page.get_by_role("treeitem", name=f"/{db_file_name_with_extension}")
    if db_file_item.count() == 0:
        db_file_item = page.get_by_role("treeitem").filter(has_text=db_file_name)
    assert db_file_item.count() > 0, f"Файл подключения '{db_file_name}' не найден в модалке!"
    db_file_item.locator("div").nth(1).click()
    time.sleep(1)
    print(f"[INFO] Клик по файлу подключения выполнен: {db_file_name_with_extension}")

    select_button = page.get_by_role("button", name="filemanager_select_button")
    assert select_button.count() > 0, "Кнопка 'Выбрать' не найдена в модалке!"
    select_button.click()
    time.sleep(1)
    print("[INFO] Клик по кнопке 'Выбрать' выполнен")

    print("[INFO] Шаг 6: Заполнение SQL запроса в поле редактора")

    sql_editor = page.get_by_role("textbox", name="editor_view").first
    assert sql_editor.is_visible(), "Поле редактора SQL не найдено!"
    print("[INFO] Поле редактора SQL найдено")

    sql_query = f"SELECT * FROM projects WHERE code = '{project_code}'"
    sql_editor.fill(sql_query)
    time.sleep(1)
    print(f"[INFO] SQL запрос введен: {sql_query}")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    if details_panel.is_visible():
        switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if switcher.is_visible():
            switcher.click()
            time.sleep(0.5)
            print("[INFO] Правый сайдбар закрыт")

    print("[INFO] Шаг 7: Настройка компонента Output")

    output_found = canvas_utils.find_component_by_title("Output", timeout=10000)
    assert output_found, "Компонент 'Output' не найден на канвасе!"
    print("[INFO] Компонент 'Output' найден и двойной клик выполнен")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт")

    data_field = page.get_by_role("textbox", name="inputs_config.data.value")
    if data_field.count() == 0:
        data_field = page.get_by_role("textbox", name="config.data")
    if data_field.count() == 0:
        data_field = page.locator(ComponentLocators.DATA_VALUE_FALLBACK)
    
    try:
        assert data_field.count() > 0, "Поле 'Данные' не найдено!"
        data_field.fill("$node.Query.data[0]")
        time.sleep(1)
        print("[INFO] Поле 'Данные' заполнено: $node.Query.data[0]")
    except Exception as e:
        print(f"[WARN] Не удалось заполнить Output.data через UI: {e}")
        _patch_query_diagram_via_api(
            project_code,
            _current_branch(page),
            "/test_flow_component/test_query.df.json",
            f"/db_connection/{db_file_name_with_extension}",
            sql_query,
            "$node.Query.data[0]",
        )
        page.reload(wait_until="networkidle")
        assert wait_for_canvas_with_refresh(page, timeout=10000, max_refreshes=1), (
            "Canvas не загрузился после API-настройки Output"
        )

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

    assert diagram_page.run_diagram(), "Диаграмма не запустилась!"
    assert diagram_page.wait_for_diagram_completion(timeout=15000), "Диаграмма не завершилась!"
    print("[INFO] Диаграмма завершилась, результат проверяем в Output")

    print("[INFO] Шаг 9: Проверка JSON данных в модальном окне")

    canvas = page.locator(CanvasLocators.CANVAS).first
    canvas.dblclick(force=True)
    time.sleep(1)
    print("[INFO] Двойной клик по канвасу выполнен")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Сайдбар открыт")

    process_tab = page.get_by_text("Процесс", exact=True)
    assert process_tab.is_visible(), "Вкладка 'Процесс' не найдена!"
    process_tab.click()
    time.sleep(1)
    print("[INFO] Переход на вкладку 'Процесс' выполнен")

    analysis_tab = page.get_by_text("Отладка", exact=True)
    assert analysis_tab.is_visible(), "Подвкладка 'Отладка' не найдена!"
    analysis_tab.click()
    time.sleep(1)
    print("[INFO] Переход на подвкладку 'Отладка' выполнен")

    full_view_button = page.get_by_role("button", name="formitem_full_view_button").nth(1)
    assert full_view_button.is_visible(), "Кнопка 'formitem_full_view_button' не найдена!"
    full_view_button.click()
    time.sleep(1)
    print("[INFO] Кнопка 'formitem_full_view_button' нажата")

    # Диагностика + fallback: в разных сборках модалка может иметь разную разметку.
    json_modal = page.locator(ModalLocators.JSON_MODAL)
    modal_overlay = page.locator('[aria-label="modal_overlay"]')
    modal_content_fallback = page.locator('[class*="Modal__Modal"] [class*="Modal__Content"]')
    json_title = page.get_by_text("Просмотр JSON", exact=False)
    try:
        json_modal.wait_for(state="visible", timeout=10000)
    except Exception:
        dialogs_count = page.locator('[role="dialog"]').count()
        overlays_count = modal_overlay.count()
        fallback_count = modal_content_fallback.count()
        title_count = json_title.count()
        print(
            f"[WARN] JSON-модалка не найдена по role=dialog, переключаемся на fallback. "
            f"dialogs={dialogs_count}, overlays={overlays_count}, fallback={fallback_count}, title_matches={title_count}"
        )
        modal_overlay.first.wait_for(state="visible", timeout=10000)
        json_modal = modal_content_fallback.first
        json_modal.wait_for(state="visible", timeout=10000)

    print("[INFO] Модальное окно 'Просмотр JSON' открыто")
    
    save_screenshot(page, f"json_modal_{project_code}")
    
    time.sleep(3)

    modal_text = json_modal.inner_text()
    print(f"[INFO] Текст в модалке (обрезан): {modal_text[:200]}...")
    assert modal_text.strip(), "Модальное окно JSON открыто, но внутри нет текста ответа"
    normalized = modal_text.replace("\xa0", " ")
    assert project_code in normalized, f"В JSON нет ожидаемого кода проекта: {project_code}"

    # Ответ отладки менялся между версиями: snake_case/camelCase, master/main, блок type=git_local без явной ветки
    has_branch_fields = ("default_branch" in normalized) or ("defaultBranch" in normalized)
    has_branch_value = ("master" in normalized) or ("main" in normalized)
    if has_branch_fields and has_branch_value:
        pass
    elif "git_local" in normalized:
        pass
    else:
        pos = normalized.find("{")
        if pos >= 0:
            try:
                data, _ = json.JSONDecoder().raw_decode(normalized[pos:])
            except json.JSONDecodeError:
                data = None

            def _walk_git_meta(o):
                if isinstance(o, dict):
                    if o.get("type") == "git_local":
                        return True
                    db = o.get("default_branch") or o.get("defaultBranch")
                    if db in ("master", "main"):
                        return True
                    return any(_walk_git_meta(v) for v in o.values())
                if isinstance(o, list):
                    return any(_walk_git_meta(x) for x in o)
                return False

            assert isinstance(data, dict) and _walk_git_meta(data), (
                f"В JSON нет git_local / default_branch(main|master). Фрагмент: {normalized[:1200]!r}"
            )
        else:
            raise AssertionError(
                f"Нет признаков репозитория в модалке (ветка или git_local). Фрагмент: {normalized[:1200]!r}"
            )

    close_button = page.locator(ModalLocators.MODAL_CLOSE_BUTTON)
    if close_button.count() > 0:
        close_button.first.click()
        time.sleep(1)
        print("[INFO] Модальное окно закрыто")

    save_screenshot(page, f"query_test_complete_{project_code}")

    print("[SUCCESS] Все шаги теста Query выполнены успешно!")
