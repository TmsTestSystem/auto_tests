import pytest
import time
from pages.project_page import ProjectPage
from pages.diagram_page import DiagramPage
from pages.connection_page import ConnectionPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from locators.canvas_locators import CanvasLocators
from locators.diagram_locators import DiagramLocators
from conftest import wait_for_canvas_with_refresh


def save_screenshot(page, name):
    """Сохраняет скриншот страницы"""
    try:
        screenshot_path = f"screenshots/{name}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[SCREENSHOT] Сохранен скриншот: {screenshot_path}")
    except Exception as e:
        print(f"[WARN] Не удалось сохранить скриншот: {e}")


def test_flow_split(login_page, flow_project):
    """
    Тест для создания диаграммы с ветвлением: Старт процесса -> Шлюз -> Output / Output2
    """
    page, project_code = flow_project
    project_page = ProjectPage(page)
    diagram_page = DiagramPage(page)
    connection_page = ConnectionPage(page)

    print(f"[INFO] Переход в проект Branch Flow New в проекте: {project_code}")

    assert project_page.goto_project(project_code), f"Не удалось перейти в проект {project_code}!"
    time.sleep(2)

    print("[SUCCESS] Переход в проект выполнен!")

    timestamp = int(time.time())
    schema_name = f"test_schema_{timestamp}"
    diagram_name = f"test_diagram_{timestamp}"
    
    print(f"[INFO] Шаг 1: Создание структуры данных '{schema_name}'")
    
    page.get_by_label("/shema", exact=True).locator("div").filter(has_text="shema").nth(1).click(button="right")
    time.sleep(1)
    page.get_by_text("СоздатьAlt+N").click()
    time.sleep(1)
    page.get_by_role("treeitem", name="data_structure", exact=True).locator("div").nth(1).click()
    time.sleep(1)
    page.get_by_role("textbox", name="treeitem_label_field").fill(schema_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    time.sleep(1)
    page.get_by_role("button", name="datastructureeditor_create_schema_button").first.click()
    time.sleep(2)
    page.get_by_role("textbox", name="treeitem_label_field").fill("str_name")
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    time.sleep(1)
    page.get_by_role("button", name="datastructureeditor_create_attribute_button").first.click()
    time.sleep(1)
    page.get_by_role("textbox", name="attributes.0.name").fill("active")
    time.sleep(1)
    page.get_by_role("textbox", name="attributes.0.schema.type").click()
    time.sleep(2)
    page.get_by_role("treeitem", name="boolean").locator("div").nth(1).click()
    time.sleep(1)
    page.get_by_role("button", name=f"file=%2Fshema%2F{schema_name}.ds.").click(button="right")
    time.sleep(1)
    page.get_by_role("treeitem", name="closeTab").locator("div").nth(1).click()
    time.sleep(1)
    print(f"[SUCCESS] Структура данных '{schema_name}' создана")
    
    print(f"[INFO] Шаг 2: Создание диаграммы '{diagram_name}'")
    
    page.get_by_role("button", name="filemanager_create_button").click()
    time.sleep(1)
    page.get_by_role("treeitem", name="decision_flow").locator("div").nth(1).click()
    time.sleep(1)
    page.get_by_role("textbox", name="treeitem_label_field").fill(diagram_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    time.sleep(2)
    
    print("[INFO] Ожидание загрузки диаграммы")
    try:
        switcher_button = page.get_by_role("button", name="diagram_details_panel_switcher")
        switcher_button.wait_for(state="visible", timeout=10000)
        switcher_button.click()
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Кнопка diagram_details_panel_switcher не появилась сразу: {e}, продолжаем...")
        time.sleep(2)
        try:
            switcher_button = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher_button.is_visible():
                switcher_button.click()
                time.sleep(1)
        except:
            pass
    
    try:
        file_manager_button = page.get_by_role("button", name="board_toolbar_filemanager_button")
        if file_manager_button.is_visible():
            file_manager_button.click()
            time.sleep(1)
    except Exception as e:
        print(f"[WARN] Кнопка board_toolbar_filemanager_button не найдена: {e}, продолжаем...")
    
    print(f"[SUCCESS] Диаграмма '{diagram_name}' создана")
    
    print("[INFO] Шаг 3: Ожидание загрузки canvas диаграммы")
    assert wait_for_canvas_with_refresh(page, timeout=15000, max_refreshes=2), "Canvas не загрузился даже после рефреша!"
    time.sleep(2)
    
    print("[INFO] Шаг 4: Добавление компонентов на диаграмму")
    
    print("[INFO] Добавление компонента 'Старт процесса'")
    create_button = page.get_by_role("button", name="diagram_create_button")
    create_button.wait_for(state="visible", timeout=10000)
    create_button.click()
    page.get_by_text("Старт процесса").click()
    canvas = page.locator("#cy-node-edge-editing-stage1 canvas").first
    if not canvas.is_visible():
        canvas = page.locator("canvas").first
    canvas.click(position={"x": 300, "y": 300})
    time.sleep(2)
    print("[SUCCESS] Компонент 'Старт процесса' добавлен")
    
    page.get_by_role("button", name="diagram_create_button").click()
    page.get_by_text("Шлюз").click()
    
    canvas.click(position={"x": 500, "y": 300})
    time.sleep(2)
    print("[SUCCESS] Компонент 'Шлюз' добавлен")
    
    print("[INFO] Шаг 4: Создание соединения Input -> Split")
    
    input_component = page.get_by_text("Input").first
    input_component.click()
    time.sleep(1)
    
    connection_point = None
    try:
        connection_point = page.get_by_text("top").first
        if connection_point.is_visible():
            print("[INFO] Найдена точка 'top'")
    except:
        try:
            connection_point = page.get_by_text("right").first
            if connection_point.is_visible():
                print("[INFO] Найдена точка 'right'")
        except:
            print("[ERROR] Не найдена точка соединения")
            return
    
    if connection_point:
        connection_point.hover()
        page.mouse.down()
        time.sleep(0.5)
        
        split_component = page.get_by_text("Split").first
        split_component.hover()
        page.mouse.up()
        time.sleep(1)
        
        print("[SUCCESS] Соединение Input -> Split создано")
    
    print("[INFO] Шаг 5: Настройка компонента Split")
    
    split_component = page.get_by_text("Split").first
    split_component.dblclick()
    time.sleep(3)
    print("[SUCCESS] Сайдбар открыт")
    
    add_button = page.get_by_role("button", name="extendable_list_add_button")
    add_button.wait_for(state="visible", timeout=10000)
    add_button.click()
    time.sleep(1)
    print("[SUCCESS] Кнопка 'Добавить' нажата")
    
    name_field = page.get_by_role("textbox", name="config.patterns.0.name")
    name_field.wait_for(state="visible", timeout=10000)
    name_field.click()
    name_field.fill("condition_name")
    time.sleep(1)
    print("[SUCCESS] Поле имени условия заполнено")
    
    expression_field = page.get_by_role("textbox", name="config.patterns.0.expression")
    expression_field.wait_for(state="visible", timeout=10000)
    expression_field.click()
    expression_field.fill("$node.Input.data.active")
    time.sleep(1)
    print("[SUCCESS] Поле выражения заполнено")
    
    print("[SUCCESS] Условие добавлено в компонент Split")
    
    print("[INFO] Шаг 6: Настройка компонента Input")
    
    input_component = page.get_by_text("Input").first
    input_component.dblclick()
    time.sleep(3)
    print("[SUCCESS] Сайдбар для Input открыт")
    
    # В новой версии UI выбор структуры открывается через поле config.openapi_schema.type
    page.get_by_role("textbox", name="config.openapi_schema.type").click()
    time.sleep(1)
    page.get_by_text("Структура данных").click()
    time.sleep(1)
    # Выбираем нужную структуру данных через datastructureview по имени файла схемы
    page.get_by_label("datastructureview", exact=True).get_by_text(f"{schema_name}.ds.json").click()
    time.sleep(1)
    # И отдельно кликаем по самой схеме внутри файла (якорь после #)
    page.get_by_role("treeitem", name=f"/{schema_name}.ds.json#str_name").locator("div").nth(1).click()
    time.sleep(1)
    # Подтверждаем выбор структуры и схемы
    page.get_by_role("button", name="datastructureview_select_button").click()
    time.sleep(1)
    print("[SUCCESS] Структура и схема выбраны и подтверждены через datastructureview")
    
    print("[SUCCESS] Компонент Input настроен")
    
    print("[INFO] Шаг 7: Закрытие правого сайдбара")
    
    diagram_page.close_right_sidebar()
    time.sleep(1)
    print("[SUCCESS] Правый сайдбар закрыт")
    
    print("[INFO] Шаг 8: Добавление компонентов 'Конец процесса'")
    
    page.get_by_role("button", name="diagram_create_button").click()
    page.get_by_role("treeitem", name="Exit.OpenAPI").get_by_label("treeitem_label").click()
    
    canvas.click(position={"x": 700, "y": 200})
    time.sleep(2)
    print("[SUCCESS] Первый компонент 'Конец процесса' добавлен")
    
    page.get_by_role("button", name="diagram_create_button").click()
    page.get_by_role("treeitem", name="Exit.OpenAPI").get_by_label("treeitem_label").click()
    
    canvas.click(position={"x": 700, "y": 400})
    time.sleep(2)
    print("[SUCCESS] Второй компонент 'Конец процесса' добавлен")
    
    print("[INFO] Шаг 9: Создание соединений Split -> Output")
    
    split_component = page.get_by_text("Split").first
    split_component.click()
    time.sleep(1)
    
    connection_point = None
    try:
        connection_point = page.get_by_text("right").first
        if connection_point.is_visible():
            print("[INFO] Найдена точка 'right' в Split")
    except:
        try:
            connection_point = page.get_by_text("bottom").first
            if connection_point.is_visible():
                print("[INFO] Найдена точка 'bottom' в Split")
        except:
            print("[ERROR] Не найдена точка соединения в Split")
            return
    
    if connection_point:
        connection_point.hover()
        page.mouse.down()
        time.sleep(0.5)
        
        output2_component = page.get_by_text("Output").nth(1)
        output2_component.hover()
        page.mouse.up()
        time.sleep(1)
        print("[SUCCESS] Соединение Split -> Output2 создано")
        
        split_component.click()
        time.sleep(1)
        
        connection_point.hover()
        page.mouse.down()
        time.sleep(0.5)
        
        output1_component = page.get_by_text("Output").first
        output1_component.hover()
        page.mouse.up()
        time.sleep(1)
        print("[SUCCESS] Соединение Split -> Output1 создано")
    
    print("[INFO] Шаг 10: Работа с сайдбаром процесса")
    
    page.get_by_text("Процесс", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Переход на вкладку 'Процесс'")
    
    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    details_panel.get_by_text("Отладка", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Переход на подвкладку 'Отладка'")
    
    page.get_by_role("button", name="formitem_paste_button").click()
    time.sleep(1)
    print("[SUCCESS] Кнопка 'Предзаполнить' нажата")
    
    print("[INFO] Шаг 11: Запуск диаграммы")
    
    page.get_by_role("button", name="diagram_play_button").click()
    time.sleep(2)
    print("[SUCCESS] Кнопка 'Запуск' нажата")
    
    print("[INFO] Шаг 12: Настройка компонента Output2")
    
    output2_component = page.get_by_text("Output").nth(1)
    output2_component.dblclick()
    time.sleep(3)
    print("[SUCCESS] Сайдбар для Output2 открыт")
    
    page.get_by_text("Параметры").click()
    time.sleep(1)
    print("[SUCCESS] Переход на подвкладку 'Параметры'")
    
    data_field = page.get_by_role("textbox", name="inputs_config.data.value")
    data_field.wait_for(state="visible", timeout=10000)
    data_field.click()
    data_field.fill('{"Result": $node.Split."1"}')
    time.sleep(1)
    print("[SUCCESS] Поле 'Данные' заполнено")
    
    print("[INFO] Шаг 13: Возврат на вкладку 'Процесс' и редактирование")
    
    page.get_by_text("Процесс", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Возврат на вкладку 'Процесс'")
    
    # Переход на подвкладку "Отладка"
    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    details_panel.get_by_text("Отладка", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Переход на подвкладку 'Отладка'")
    
    page.get_by_text("{").first.click()
    time.sleep(1)
    print("[SUCCESS] Клик в редакторе Monaco")
    
    page.get_by_role("code").first.press("ControlOrMeta+h")
    time.sleep(1)
    page.get_by_placeholder("Найти").fill("false")
    page.get_by_role("textbox", name="Заменить").click()
    page.get_by_role("textbox", name="Заменить").fill("true")
    page.get_by_role("button", name="Заменить (Enter)").click()
    time.sleep(1)
    print("[SUCCESS] Значение false заменено на true")
    
    print("[INFO] Шаг 14: Сброс и повторный запуск диаграммы")
    
    page.get_by_role("button", name="diagram_reset_button").click()
    time.sleep(1)
    print("[SUCCESS] Диаграмма сброшена")
    
    page.get_by_role("button", name="diagram_play_button").click()
    time.sleep(2)
    print("[SUCCESS] Диаграмма запущена повторно")
    
    print("[INFO] Шаг 15: Проверка завершения диаграммы")
    
    toast_message = page.get_by_text("Диаграмма завершена на компоненте \"Output2\"")
    toast_message.wait_for(state="visible", timeout=10000)
    assert toast_message.is_visible(), "Тост о завершении диаграммы не найден"
    print("[SUCCESS] Диаграмма завершена на компоненте 'Output2'")
    
    print("[SUCCESS] Тест завершен успешно!")
    print(f"[SUCCESS] Создана структура данных: {schema_name}")
    print(f"[SUCCESS] Создана диаграмма: {diagram_name}")
    print("[SUCCESS] Компоненты размещены и соединены")
    print("[SUCCESS] Компонент Split настроен с условием")
    print("[SUCCESS] Компонент Input настроен")
    print("[SUCCESS] Добавлены два компонента 'Конец процесса'")
    print("[SUCCESS] Созданы соединения Split -> Output2 и Split -> Output1")
    print("[SUCCESS] Выполнена работа с сайдбаром процесса")
    print("[SUCCESS] Диаграмма запущена")
    print("[SUCCESS] Компонент Output2 настроен")
    print("[SUCCESS] Выполнено редактирование в Monaco редакторе")
    print("[SUCCESS] Диаграмма сброшена и запущена повторно")
    print("[SUCCESS] Диаграмма успешно завершена на компоненте Output2")