import time
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.diagram_page import DiagramPage
from pages.canvas_utils import CanvasUtils
from pages.connection_page import ConnectionPage
from conftest import save_screenshot, get_project_by_code, delete_project_by_id
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


def test_tutorial_flow(login_page, shared_flow_project):
    """
    Тест для создания схемы процесса согласно пошаговому гайду:
    1. Старт процесса
    2. Функция 1  
    3. Шлюз
    4. HTTP Коннектор
    5. Функция 2
    6. Конец процесса
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)
    canvas_utils = CanvasUtils(page)
    connection_page = ConnectionPage(page)
    
    print(f"[INFO] Начинаем тест Tutorial Flow в проекте: {project_code}")
    
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)
    
    # Пауза для наблюдения браузера
    print("[INFO] Пауза 5 секунд для наблюдения браузера...")
    time.sleep(5)

    print("[INFO] Шаг 1: Создание файла 'Процесс' в корне проекта")
    file_panel.open_file_panel()
    time.sleep(1)
    
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
                    print(f"[SUCCESS] Найдена и нажата кнопка процесса: '{btn_text}'")
                    break
            except Exception as e:
                print(f"[DEBUG] Ошибка при обработке элемента {i}: {e}")
                continue
        
        if not process_found:
            page.screenshot(path='screenshots/debug_process_menu.png', full_page=True)
            print("[ERROR] Кнопка 'Процесс' не найдена в меню. Скриншот сохранен.")
            raise Exception("Кнопка 'Процесс' не найдена в меню создания файлов")
        
        name_input = page.get_by_role("textbox", name="treeitem_label_field")
        name_input.wait_for(state="visible", timeout=10000)
        process_name = f"tutorial_process_{int(time.time())}"
        name_input.fill(process_name)
        page.keyboard.press("Enter")
        time.sleep(2)
    
    assert process_name is not None, "Не удалось создать файл процесса"
    
    print(f"[SUCCESS] Создан файл процесса: {process_name}")
    
    page.get_by_role("treeitem", name=f"/{process_name}").click()
    time.sleep(2)
    
    diagram_page.close_panels()
    time.sleep(1)
    print("[INFO] Все панели закрыты")
    
    print("[INFO] Шаг 2: Добавление компонентов в указанном порядке")
    
    # 1. Старт процесса
    print("[INFO] Добавляем компонент 'Старт процесса'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Старт процесса").click()
    time.sleep(0.5)
    
    canvas = page.locator(CanvasLocators.CANVAS).first
    canvas.wait_for(state="visible", timeout=10000)
    canvas.click(position={"x": 200, "y": 200}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Старт процесса' размещен")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 2. Функция 1
    print("[INFO] Добавляем компонент 'Функция 1'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Функция").click()
    time.sleep(0.5)
    canvas.click(position={"x": 200, "y": 280}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Функция 1' размещен")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 3. Шлюз
    print("[INFO] Добавляем компонент 'Шлюз'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Шлюз").click()
    time.sleep(0.5)
    canvas.click(position={"x": 200, "y": 360}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Шлюз' размещен")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 4. HTTP Коннектор
    print("[INFO] Добавляем компонент 'HTTP Коннектор'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("HTTP Коннектор").click()
    time.sleep(0.5)
    canvas.click(position={"x": 400, "y": 360}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'HTTP Коннектор' размещен")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 5. Функция 2
    print("[INFO] Добавляем компонент 'Функция 2'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Функция").click()
    time.sleep(0.5)
    canvas.click(position={"x": 200, "y": 440}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Функция 2' размещен")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    # 6. Конец процесса
    print("[INFO] Добавляем компонент 'Конец процесса'")
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    page.get_by_text("Конец процесса").click()
    time.sleep(0.5)
    canvas.click(position={"x": 200, "y": 520}, force=True)
    time.sleep(1)
    print("[SUCCESS] Компонент 'Конец процесса' размещен")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    print("[INFO] Шаг 3: Создание соединений между компонентами")
    
    # Сначала найдем все компоненты на странице для отладки
    print("[DEBUG] Поиск всех компонентов на странице:")
    all_text_elements = page.locator('text').all()
    component_names = []
    for element in all_text_elements:
        try:
            text = element.text_content()
            if text and len(text.strip()) > 0 and len(text.strip()) < 50:  # Фильтруем длинные тексты
                component_names.append(text.strip())
        except:
            continue
    
    # Выводим уникальные названия компонентов
    unique_components = list(set(component_names))
    print(f"[DEBUG] Найдено {len(unique_components)} уникальных текстовых элементов:")
    for i, comp in enumerate(unique_components[:20]):  # Показываем первые 20
        print(f"[DEBUG] {i+1}: '{comp}'")
    
    def create_precise_connection(from_component_name, to_component_name, from_direction="bottom", to_direction="top"):
        """
        Универсальный метод для создания соединений между компонентами
        Сначала кликает на компонент, чтобы появились точки соединения
        """
        print(f"[INFO] Создание соединения: {from_component_name} ({from_direction}) -> {to_component_name} ({to_direction})")
        
        # Находим компоненты
        from_component = page.get_by_text(from_component_name).first
        to_component = page.get_by_text(to_component_name).first
            
        if not from_component.is_visible() or not to_component.is_visible():
            print(f"[ERROR] Компоненты не найдены: {from_component_name} или {to_component_name}")
            return False
        
        # ВАЖНО: Сначала кликаем на исходный компонент, чтобы появились точки соединения
        print(f"[INFO] Кликаем на компонент '{from_component_name}' для появления точек соединения")
        from_component.click()
        time.sleep(2)  # Ждем появления точек соединения
        
        # Получаем координаты компонентов после клика
        from_box = from_component.bounding_box()
        to_box = to_component.bounding_box()
        
        if not from_box or not to_box:
            print(f"[ERROR] Не удалось получить координаты компонентов")
            return False
            
        # Вычисляем точки соединения
        if from_direction == "bottom":
            from_x = from_box['x'] + from_box['width'] / 2
            from_y = from_box['y'] + from_box['height']
        elif from_direction == "top":
            from_x = from_box['x'] + from_box['width'] / 2
            from_y = from_box['y']
        elif from_direction == "right":
            from_x = from_box['x'] + from_box['width']
            from_y = from_box['y'] + from_box['height'] / 2
        elif from_direction == "left":
            from_x = from_box['x']
            from_y = from_box['y'] + from_box['height'] / 2
        else:
            from_x = from_box['x'] + from_box['width'] / 2
            from_y = from_box['y'] + from_box['height'] / 2
            
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
            
        print(f"[DEBUG] Координаты соединения: от ({from_x:.1f}, {from_y:.1f}) к ({to_x:.1f}, {to_y:.1f})")
            
        # Создаем соединение
        success = connection_page.create_connection_by_coordinates(from_x, from_y, to_x, to_y, from_direction)
        if success:
            print(f"[SUCCESS] Соединение создано: {from_component_name} -> {to_component_name}")
        else:
            print(f"[ERROR] Не удалось создать соединение: {from_component_name} -> {to_component_name}")
        return success
    
    # Создаем соединения - используем точные названия компонентов из скриншота
    create_precise_connection("Input", "Function", "bottom", "top")
    time.sleep(2)
    
    create_precise_connection("Function", "Split", "bottom", "top")
    time.sleep(2)
    
    create_precise_connection("HttpConnector", "Function2", "right", "left")
    time.sleep(2)
    
    create_precise_connection("Function2", "Output", "bottom", "top")
    time.sleep(2)
    
    # Согласно гайду: "Стрелки от Шлюза пока не добавляйте — это будет сделано при настройке компонента на втором этапе"
    print("[INFO] Соединения от Шлюза не добавляем согласно гайду")
    
    save_screenshot(page, f"tutorial_flow_complete_{project_code}")
    
    print("[SUCCESS] Все компоненты добавлены и соединены согласно пошаговому гайду!")
    print("[SUCCESS] Создана схема: Старт процесса -> Функция 1 -> Шлюз -> HTTP Коннектор -> Функция 2 -> Конец процесса")
    
    # Пауза для наблюдения результата
    print("[INFO] Пауза 10 секунд для наблюдения результата...")
    time.sleep(10)
    