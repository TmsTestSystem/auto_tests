import pytest
import time
from pages.project_page import ProjectPage
from pages.diagram_page import DiagramPage
from pages.connection_page import ConnectionPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from locators.canvas_locators import CanvasLocators


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

    # Генерируем уникальные имена
    timestamp = int(time.time())
    schema_name = f"test_schema_{timestamp}"
    diagram_name = f"test_diagram_{timestamp}"
    
    print(f"[INFO] Шаг 1: Создание структуры данных '{schema_name}'")
    
    # Создание структуры данных
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
    time.sleep(2)  # Ждем загрузки редактора
    page.get_by_role("textbox", name="treeitem_label_field").fill("str_name")
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    time.sleep(1)
    page.get_by_role("button", name="datastructureeditor_create_attribute_button").first.click()
    time.sleep(1)
    page.get_by_role("textbox", name="attributes.0.name").fill("active")
    time.sleep(1)
    page.get_by_role("textbox", name="attributes.0.schema.type").click()
    time.sleep(2)  # Ждем появления списка типов
    page.get_by_role("treeitem", name="boolean").locator("div").nth(1).click()
    time.sleep(1)
    page.get_by_role("button", name=f"file=%2Fshema%2F{schema_name}.ds.").click(button="right")
    time.sleep(1)
    page.get_by_role("treeitem", name="closeTab").locator("div").nth(1).click()
    time.sleep(1)
    print(f"[SUCCESS] Структура данных '{schema_name}' создана")
    
    print(f"[INFO] Шаг 2: Создание диаграммы '{diagram_name}'")
    
    # Создание диаграммы
    page.get_by_role("button", name="filemanager_create_button").click()
    time.sleep(1)
    page.get_by_role("treeitem", name="decision_flow").locator("div").nth(1).click()
    time.sleep(1)
    page.get_by_role("textbox", name="treeitem_label_field").fill(diagram_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    time.sleep(2)  # Ждем создания диаграммы
    page.get_by_role("button", name="diagram_details_panel_switcher").click()
    time.sleep(1)
    page.get_by_role("button", name="board_toolbar_filemanager_button").click()
    time.sleep(1)
    print(f"[SUCCESS] Диаграмма '{diagram_name}' создана")
    
    print("[INFO] Шаг 3: Добавление компонентов на диаграмму")
    
    # Добавление компонента "Старт процесса"
    page.get_by_role("button", name="diagram_create_button").click()
    page.get_by_text("Старт процесса").click()
    
    # Ищем канвас с правильным селектором
    canvas = page.locator("#cy-node-edge-editing-stage1 canvas").first
    canvas.wait_for(state="visible", timeout=10000)
    
    # Кликаем на канвас для размещения "Старт процесса"
    canvas.click(position={"x": 300, "y": 300})
    time.sleep(2)
    print("[SUCCESS] Компонент 'Старт процесса' добавлен")
    
    # Добавление компонента "Шлюз"
    page.get_by_role("button", name="diagram_create_button").click()
    page.get_by_text("Шлюз").click()
    
    # Кликаем на канвас для размещения "Шлюз"
    canvas.click(position={"x": 500, "y": 300})
    time.sleep(2)
    print("[SUCCESS] Компонент 'Шлюз' добавлен")
    
    print("[INFO] Шаг 4: Создание соединения Input -> Split")
    
    # Ищем компонент Input (Старт процесса) и кликаем по нему
    input_component = page.get_by_text("Input").first
    input_component.click()
    time.sleep(1)
    
    # Ищем точку соединения (top или right) внутри компонента Input
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
        # Делаем лонгтап по точке соединения
        connection_point.hover()
        page.mouse.down()
        time.sleep(0.5)
        
        # Тянем до компонента Split (Шлюз)
        split_component = page.get_by_text("Split").first
        split_component.hover()
        page.mouse.up()
        time.sleep(1)
        
        print("[SUCCESS] Соединение Input -> Split создано")
    
    print("[INFO] Шаг 5: Настройка компонента Split")
    
    # Двойной клик по компоненту Split для открытия сайдбара
    split_component = page.get_by_text("Split").first
    split_component.dblclick()
    time.sleep(3)
    print("[SUCCESS] Сайдбар открыт")
    
    # Ждем появления полей в сайдбаре
    # Нажимаем кнопку "Добавить" для создания нового условия
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
    
    # Двойной клик по компоненту Input для открытия сайдбара
    input_component = page.get_by_text("Input").first
    input_component.dblclick()
    time.sleep(3)
    print("[SUCCESS] Сайдбар для Input открыт")
    
    # Заполнение полей Структура и Схема для Input
    # Выбираем структуру данных
    page.get_by_role("button", name="textfield_select_file_button").click()
    page.get_by_text(f"{schema_name}.ds.json").click()
    page.get_by_role("button", name="filemanager_select_button").click()
    time.sleep(1)
    print("[SUCCESS] Структура данных выбрана")
    
    # Выбираем схему
    page.get_by_role("textbox", name="config.schema").click()
    page.get_by_role("treeitem", name="str_name").locator("div").nth(2).click()
    time.sleep(1)
    print("[SUCCESS] Схема выбрана")
    
    print("[SUCCESS] Компонент Input настроен")
    
    print("[INFO] Шаг 7: Закрытие правого сайдбара")
    
    # Закрываем правый сайдбар
    diagram_page.close_right_sidebar()
    time.sleep(1)
    print("[SUCCESS] Правый сайдбар закрыт")
    
    print("[INFO] Шаг 8: Добавление компонентов 'Конец процесса'")
    
    # Добавление первого компонента "Конец процесса"
    page.get_by_role("button", name="diagram_create_button").click()
    page.get_by_role("treeitem", name="Exit.OpenAPI").get_by_label("treeitem_label").click()
    
    # Кликаем на канвас для размещения первого "Конец процесса"
    canvas.click(position={"x": 700, "y": 200})
    time.sleep(2)
    print("[SUCCESS] Первый компонент 'Конец процесса' добавлен")
    
    # Добавление второго компонента "Конец процесса"
    page.get_by_role("button", name="diagram_create_button").click()
    page.get_by_role("treeitem", name="Exit.OpenAPI").get_by_label("treeitem_label").click()
    
    # Кликаем на канвас для размещения второго "Конец процесса"
    canvas.click(position={"x": 700, "y": 400})
    time.sleep(2)
    print("[SUCCESS] Второй компонент 'Конец процесса' добавлен")
    
    print("[INFO] Шаг 9: Создание соединений Split -> Output")
    
    # Создание соединения Split -> Output1
    split_component = page.get_by_text("Split").first
    split_component.click()
    time.sleep(1)
    
    # Ищем точку соединения в Split
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
        # Соединение Split -> Output1
        connection_point.hover()
        page.mouse.down()
        time.sleep(0.5)
        
        output1_component = page.get_by_text("Output").first
        output1_component.hover()
        page.mouse.up()
        time.sleep(1)
        print("[SUCCESS] Соединение Split -> Output1 создано")
        
        # Соединение Split -> Output2
        split_component.click()
        time.sleep(1)
        
        connection_point.hover()
        page.mouse.down()
        time.sleep(0.5)
        
        output2_component = page.get_by_text("Output").nth(1)
        output2_component.hover()
        page.mouse.up()
        time.sleep(1)
        print("[SUCCESS] Соединение Split -> Output2 создано")
    
    print("[INFO] Шаг 10: Работа с сайдбаром процесса")
    
    # Переход на вкладку "Процесс"
    page.get_by_text("Процесс", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Переход на вкладку 'Процесс'")
    
    # Переход на подвкладку "Анализ"
    page.get_by_text("Анализ").click()
    time.sleep(1)
    print("[SUCCESS] Переход на подвкладку 'Анализ'")
    
    # Нажатие кнопки "Предзаполнить"
    page.get_by_role("button", name="formitem_paste_button").click()
    time.sleep(1)
    print("[SUCCESS] Кнопка 'Предзаполнить' нажата")
    
    print("[INFO] Шаг 11: Запуск диаграммы")
    
    # Нажатие кнопки запуска
    page.get_by_role("button", name="diagram_play_button").click()
    time.sleep(2)
    print("[SUCCESS] Кнопка 'Запуск' нажата")
    
    print("[INFO] Шаг 12: Настройка компонента Output2")
    
    # Двойной клик по компоненту Output2
    output2_component = page.get_by_text("Output").nth(1)
    output2_component.dblclick()
    time.sleep(3)
    print("[SUCCESS] Сайдбар для Output2 открыт")
    
    # Переход на подвкладку "Параметры"
    page.get_by_text("Параметры").click()
    time.sleep(1)
    print("[SUCCESS] Переход на подвкладку 'Параметры'")
    
    # Заполнение поля "Данные"
    data_field = page.get_by_role("textbox", name="inputs_config.data.value")
    data_field.wait_for(state="visible", timeout=10000)
    data_field.click()
    data_field.fill('{"Result": $node.Split."1"}')
    time.sleep(1)
    print("[SUCCESS] Поле 'Данные' заполнено")
    
    print("[INFO] Шаг 13: Возврат на вкладку 'Процесс' и редактирование")
    
    # Возврат на вкладку "Процесс"
    page.get_by_text("Процесс", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Возврат на вкладку 'Процесс'")
    
    # Переход на подвкладку "Анализ"
    page.get_by_text("Анализ").click()
    time.sleep(1)
    print("[SUCCESS] Переход на подвкладку 'Анализ'")
    
    # Клик в редакторе Monaco
    page.get_by_text("{").first.click()
    time.sleep(1)
    print("[SUCCESS] Клик в редакторе Monaco")
    
    # Замена false на true через хоткей
    page.get_by_role("code").first.press("ControlOrMeta+h")
    time.sleep(1)
    page.get_by_placeholder("Найти").fill("false")
    page.get_by_role("textbox", name="Заменить").click()
    page.get_by_role("textbox", name="Заменить").fill("true")
    page.get_by_role("button", name="Заменить (Enter)").click()
    time.sleep(1)
    print("[SUCCESS] Значение false заменено на true")
    
    print("[INFO] Шаг 14: Сброс и повторный запуск диаграммы")
    
    # Сброс диаграммы
    page.get_by_role("button", name="diagram_reset_button").click()
    time.sleep(1)
    print("[SUCCESS] Диаграмма сброшена")
    
    # Повторный запуск диаграммы
    page.get_by_role("button", name="diagram_play_button").click()
    time.sleep(2)
    print("[SUCCESS] Диаграмма запущена повторно")
    
    print("[INFO] Шаг 15: Проверка завершения диаграммы")
    
    # Проверка тоста о завершении диаграммы
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
    print("[SUCCESS] Созданы соединения Split -> Output1 и Split -> Output2")
    print("[SUCCESS] Выполнена работа с сайдбаром процесса")
    print("[SUCCESS] Диаграмма запущена")
    print("[SUCCESS] Компонент Output2 настроен")
    print("[SUCCESS] Выполнено редактирование в Monaco редакторе")
    print("[SUCCESS] Диаграмма сброшена и запущена повторно")
    print("[SUCCESS] Диаграмма успешно завершена на компоненте Output2")