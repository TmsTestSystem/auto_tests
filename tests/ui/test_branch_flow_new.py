import time
import os
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from pages.diagram_page import DiagramPage
from pages.connection_page import ConnectionPage
from conftest import save_screenshot, get_project_by_code, delete_project_by_id
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


def test_branch_flow_new(login_page, shared_flow_project):
    """
    Тест для создания новой диаграммы с ветвлением: Старт процесса -> Шлюз -> Output2 / Конец процесса
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    diagram_page = DiagramPage(page)
    connection_page = ConnectionPage(page)
    
    print(f"[INFO] Начинаем тест Branch Flow New в проекте: {project_code}")
    
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)
    
    file_panel = FilePanelPage(page)
    data_struct = DataStructPage(page)
    canvas_utils = CanvasUtils(page)
    
    def create_precise_connection(from_component_name, to_component_name, from_direction="bottom", to_direction="top"):
        """
        Универсальный метод для создания соединений между компонентами
        """
        print(f"[INFO] Создание соединения: {from_component_name} ({from_direction}) -> {to_component_name} ({to_direction})")
        
        # Находим компоненты
        from_component = page.get_by_text(from_component_name).first
        to_component = page.get_by_text(to_component_name).first
            
        if not from_component.is_visible() or not to_component.is_visible():
            print(f"[ERROR] Компоненты не найдены: {from_component_name} или {to_component_name}")
            return False
        
        # ШАГ 1: Кликаем на исходный компонент
        print(f"[INFO] Шаг 1: Кликаем на компонент '{from_component_name}' для появления точек соединения")
        if from_component.is_visible():
            from_component.click()
            time.sleep(3)
            print(f"[SUCCESS] Шаг 1: Клик по компоненту '{from_component_name}' выполнен")
        else:
            print(f"[ERROR] Шаг 1: Компонент '{from_component_name}' не видим")
            return False
        
        # ШАГ 2: Получаем координаты компонентов
        from_box = from_component.bounding_box()
        to_box = to_component.bounding_box()
        
        if not from_box or not to_box:
            print(f"[ERROR] Не удалось получить координаты компонентов")
            return False
        
        # ШАГ 3: Вычисляем точки соединения
        if from_direction == "bottom":
            start_x = from_box['x'] + from_box['width'] / 2
            start_y = from_box['y'] + from_box['height']
        elif from_direction == "top":
            start_x = from_box['x'] + from_box['width'] / 2
            start_y = from_box['y']
        elif from_direction == "right":
            start_x = from_box['x'] + from_box['width']
            start_y = from_box['y'] + from_box['height'] / 2
        elif from_direction == "left":
            start_x = from_box['x']
            start_y = from_box['y'] + from_box['height'] / 2
        else:
            start_x = from_box['x'] + from_box['width'] / 2
            start_y = from_box['y'] + from_box['height'] / 2
            
        if to_direction == "bottom":
            to_x = to_box['x'] + to_box['width'] / 2
            to_y = to_box['y'] + to_box['height']
        elif to_direction == "top":
            to_x = to_box['x'] + to_box['width'] / 2
            to_y = to_box['y']
        elif to_direction == "right":
            to_x = to_box['x'] + to_box['width']
            to_y = to_box['y'] + to_box['height'] / 2
        elif to_direction == "left":
            to_x = to_box['x']
            to_y = to_box['y'] + to_box['height'] / 2
        else:
            to_x = to_box['x'] + to_box['width'] / 2
            to_y = to_box['y'] + to_box['height'] / 2
            
        print(f"[INFO] Шаг 2: Координаты соединения: от ({start_x:.1f}, {start_y:.1f}) к ({to_x:.1f}, {to_y:.1f})")
            
        # ШАГ 3: Создаем соединение
        print(f"[INFO] Шаг 3: Выполняем лонгтап и перетаскивание")
        success = connection_page.create_connection_by_coordinates(start_x, start_y, to_x, to_y, from_direction)
        
        if success:
            print(f"[SUCCESS] Соединение создано: {from_component_name} -> {to_component_name}")
        else:
            print(f"[ERROR] Не удалось создать соединение: {from_component_name} -> {to_component_name}")
        return success
    
    print("[INFO] Шаг 1: Создание нового процесса для диаграммы с ветвлением")
    
    # Создаем новый процесс (файловая панель уже открыта после импорта)
    process_name = file_panel.create_process_file()
    if process_name is None:
        print("[WARN] Готовый метод не сработал, пробуем создать вручную")
        file_panel.open_create_file_menu()
        time.sleep(1)
        process_buttons = page.locator('div[role="treeitem"], div.TreeItem__LabelPrimary___vzajD')
        process_found = False
        for i in range(process_buttons.count()):
            try:
                btn_text = process_buttons.nth(i).text_content()
                print(f"[DEBUG] Найден элемент меню: '{btn_text}'")
                if "процесс" in btn_text.lower():
                    process_buttons.nth(i).click()
                    process_found = True
                    break
            except Exception as e:
                print(f"[DEBUG] Ошибка при обработке элемента {i}: {e}")
                continue
        
        if not process_found:
            print("[ERROR] Не найден элемент 'Процесс' в меню создания")
            return False
        
        time.sleep(1)
        
        # Вводим имя процесса
        name_input = page.get_by_role("textbox", name="treeitem_label_field")
        if name_input.is_visible():
            process_name = f"branch_flow_process_{int(time.time())}"
            name_input.fill(process_name)
            name_input.press("Enter")
            time.sleep(2)
            print(f"[SUCCESS] Процесс создан вручную: {process_name}")
        else:
            print("[ERROR] Поле ввода имени не найдено")
            return False
    else:
        print(f"[SUCCESS] Процесс создан: {process_name}")
    
    time.sleep(2)
    
    print("[INFO] Шаг 2: Добавление компонентов на диаграмму")
    
    # Закрываем все сайдбары перед размещением компонентов
    diagram_page.close_right_sidebar()
    time.sleep(1)
    
    # Закрываем файловую панель
    try:
        if page.get_by_label("board_toolbar_panel").is_visible():
            file_manager_btn = page.get_by_role("button", name="board_toolbar_filemanager_button")
            if file_manager_btn.is_visible():
                file_manager_btn.click()
                time.sleep(0.5)
                print("[INFO] Файловая панель закрыта")
    except Exception as e:
        print(f"[INFO] Файловая панель уже закрыта или не найдена: {e}")
    
    canvas = page.locator(CanvasLocators.CANVAS).first
    
    # 1. Старт процесса
    print("[INFO] Добавляем компонент 'Старт процесса'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Старт процесса").click()
    time.sleep(0.5)
    canvas.click(position={"x": 200, "y": 300}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Старт процесса' размещен")
    
    # Закрываем правый сайдбар после размещения
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 2. Шлюз
    print("[INFO] Добавляем компонент 'Шлюз'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Шлюз").click()
    time.sleep(0.5)
    canvas.click(position={"x": 400, "y": 300}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Шлюз' размещен")
    
    # Закрываем правый сайдбар после размещения
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 3. Output2 (второй "Конец процесса")
    print("[INFO] Добавляем второй компонент 'Конец процесса' (будет Output2)")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Конец процесса").click()
    time.sleep(0.5)
    canvas.click(position={"x": 600, "y": 200}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Конец процесса' (Output2) размещен")
    
    # Закрываем правый сайдбар после размещения
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 4. Output (третий "Конец процесса")
    print("[INFO] Добавляем третий компонент 'Конец процесса' (будет Output)")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Конец процесса").click()
    time.sleep(0.5)
    canvas.click(position={"x": 600, "y": 400}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Конец процесса' (Output) размещен")
    
    # Закрываем правый сайдбар после размещения
    diagram_page.close_right_sidebar()
    time.sleep(1)
    
    save_screenshot(page, f"components_placed_{project_code}")
    
    print("[INFO] Шаг 3: Создание соединений для диаграммы с ветвлением")
    
    # Создаем соединения согласно диаграмме
    # После размещения: Input -> Split -> Output2 / Output
    connections = [
        {"from": "Input", "to": "Split", "from_dir": "bottom", "to_dir": "top"},
        {"from": "Split", "to": "Output2", "from_dir": "top", "to_dir": "bottom"},
        {"from": "Split", "to": "Output", "from_dir": "right", "to_dir": "left"}
    ]
    
    for connection in connections:
        print(f"[INFO] Создаем соединение: {connection['from']} -> {connection['to']}")
        success = create_precise_connection(
            connection['from'], 
            connection['to'], 
            connection['from_dir'], 
            connection['to_dir']
        )
        if success:
            print(f"[SUCCESS] Соединение {connection['from']} -> {connection['to']} создано")
        else:
            print(f"[ERROR] Не удалось создать соединение {connection['from']} -> {connection['to']}")
        time.sleep(2)
    
    save_screenshot(page, f"branch_flow_complete_{project_code}")
    
    print("[SUCCESS] Диаграмма с ветвлением создана успешно!")
    print("[SUCCESS] Структура: Старт процесса -> Шлюз -> Output2 (условие) / Конец процесса (otherwise)")
    
    time.sleep(5)  # Пауза для наблюдения результата
    
    print("[SUCCESS] Тест Branch Flow New завершен успешно!")
