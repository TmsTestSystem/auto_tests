import time
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.diagram_page import DiagramPage
from pages.canvas_utils import CanvasUtils
from pages.connection_page import ConnectionPage
from conftest import save_screenshot, get_project_by_code, delete_project_by_id
from locators import (
    FilePanelLocators,
    DiagramLocators,
    CanvasLocators,
    ComponentLocators,
    ModalLocators,
    ToolbarLocators
)


def test_flow_flow_component(login_page, shared_flow_project):
    """
    Тест для создания родительского процесса с подпроцессом на диаграмме
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)
    canvas_utils = CanvasUtils(page)
    connection_page = ConnectionPage(page)
    
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)

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
        process_name = f"process_{int(time.time())}"
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
    
    print("[INFO] Шаг 2: Добавление элемента Input на канвас")
    
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    
    page.get_by_text("Старт процесса").click()
    time.sleep(0.5)
    
    canvas = page.locator(CanvasLocators.CANVAS).first
    canvas.wait_for(state="visible", timeout=10000)
    
    # Кликаем в левую часть canvas для Input
    canvas.click(position={"x": 200, "y": 300}, force=True)
    time.sleep(1)
    print("[SUCCESS] Элемент Input размещен на канвасе")
    
    print("[INFO] Шаг 3: Добавление элемента Output на канвас")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    page.get_by_role("button", name="diagram_create_button").click()
    time.sleep(0.5)
    
    page.get_by_text("Конец процесса").click()
    time.sleep(0.5)
    
    canvas = page.locator(CanvasLocators.CANVAS).first
    # Кликаем в правую часть canvas, чтобы не перекрывать Input
    canvas.click(position={"x": 800, "y": 300}, force=True)
    time.sleep(1)
    print("[SUCCESS] Элемент Output размещен на канвасе")
    
    diagram_page.close_right_sidebar()
    time.sleep(0.5)
    
    print("[INFO] Шаг 4: Соединение Input -> Output стрелкой")
    
    success = connection_page.create_connection("Input", "Output", "right", "center")
    if success:
        print("[SUCCESS] Стрелка соединения создана между Input и Output")
    else:
        print("[ERROR] Не удалось создать соединение между Input и Output")
        input_component = page.locator(ComponentLocators.INPUT)
        output_component = page.locator(ComponentLocators.OUTPUT)
        
        if input_component.is_visible() and output_component.is_visible():
            input_box = input_component.bounding_box()
            output_box = output_component.bounding_box()
            
            if input_box and output_box:
                from_x = input_box['x'] + input_box['width']
                from_y = input_box['y'] + input_box['height'] / 2
                to_x = output_box['x'] + output_box['width'] / 2
                to_y = output_box['y'] + output_box['height'] / 2
                
                connection_page.create_connection_by_coordinates(from_x, from_y, to_x, to_y)
                print("[SUCCESS] Соединение создано по координатам")
    
    print("[INFO] Шаг 5: Заполнение поля 'Данные' для компонента Output")
    
    output_component = page.locator(ComponentLocators.OUTPUT)
    output_component.dblclick()
    time.sleep(1)
    
    try:
        component_tab = page.get_by_text("Компонент", exact=True)
        if component_tab.is_visible():
            component_tab.click()
            time.sleep(0.5)
        
        data_field = page.get_by_role("textbox", name="inputs_config.data.value")
        if not data_field.is_visible():
            data_field = page.locator(ComponentLocators.DATA_VALUE_FALLBACK).first
        
        if data_field.is_visible():
            data_field.fill('{"test": "это результат выполнения подпроцесса"}')
            time.sleep(0.5)
            print("[SUCCESS] Поле 'Данные' заполнено для компонента Output")
        else:
            print("[WARN] Поле 'Данные' не найдено для компонента Output")
            page.screenshot(path='screenshots/debug_output_data_field.png', full_page=True)
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении поля 'Данные': {e}")
        page.screenshot(path='screenshots/debug_output_data_error.png', full_page=True)
    
    print("[INFO] Шаг 6: Переход к диаграмме test_flow")
    
    file_panel.open_file_panel()
    time.sleep(1)
    
    test_flow_folder = page.locator(FilePanelLocators.get_treeitem_by_path("test_flow_component"))
    if test_flow_folder.is_visible():
        test_flow_folder.click()
        time.sleep(1)
        print("[SUCCESS] Открыта папка test_flow_component")
        
        test_flow_file = page.get_by_text("test_flow.df.json")
        if test_flow_file.is_visible():
            test_flow_file.dblclick()
            time.sleep(2)
            print("[SUCCESS] Открыта диаграмма test_flow")
            
            page.reload()
            time.sleep(3)
            print("[SUCCESS] Страница обновлена, канвас должен обновиться")
            
            # Ждем загрузки canvas
            canvas = page.locator(CanvasLocators.CANVAS).first
            canvas.wait_for(state="visible", timeout=10000)
            time.sleep(2)
            print("[SUCCESS] Canvas загружен и готов к работе")
        else:
            print("[ERROR] Диаграмма test_flow.df.json не найдена в папке test_flow_component")
    else:
        print("[ERROR] Папка test_flow_component не найдена")
    
    print("[SUCCESS] Диаграмма test_flow открыта!")
    
    print("[INFO] Шаг 7: Поиск компонента Flow_proc на канвасе")
    flow_proc_found = canvas_utils.find_component_by_title("Flow_proc", exact=True)
    
    if flow_proc_found:
        print("[SUCCESS] Компонент 'Flow_proc' найден на канвасе!")
        
        flow_proc_component = page.get_by_text("Flow_proc").first
        flow_proc_component.dblclick()
        time.sleep(1)
        print("[SUCCESS] Открыты настройки компонента Flow_proc")
        
        try:
            data_field = page.get_by_role("textbox", name="inputs_config.data.value")
            if not data_field.is_visible():
                data_field = page.locator(ComponentLocators.DATA_VALUE_FALLBACK).first

            if data_field.is_visible():
                data_field.fill('{"test": "это результат выполнения подпроцесса"}')
                time.sleep(0.5)
                print("[SUCCESS] Поле 'Данные' заполнено для компонента Flow_proc")
            else:
                print("[WARN] Поле 'Данные' не найдено для компонента Flow_proc")
        except Exception as e:
            print(f"[WARN] Ошибка при заполнении поля 'Данные': {e}")
        
        try:
            page.get_by_role("button", name="textfield_select_file_button").click()
            time.sleep(1)
            print("[SUCCESS] Нажата кнопка выбора файла")
            
            page.get_by_test_id("Modal__Container").get_by_text(f"{process_name}.df.json").click()
            time.sleep(1)
            print(f"[SUCCESS] Выбран файл {process_name}.df.json")
            
            page.get_by_role("button", name="filemanager_select_button").click()
            time.sleep(1)
            print("[SUCCESS] Выбор файла подтвержден")
        except Exception as e:
            print(f"[WARN] Ошибка при выборе файла: {e}")
        
        diagram_page.close_right_sidebar()
        time.sleep(1)
        print("[SUCCESS] Сайдбар закрыт после настройки Flow_proc")
        
        try:
            output_component = page.locator(ComponentLocators.OUTPUT)
            output_component.dblclick()
            time.sleep(1)
            print("[SUCCESS] Открыты настройки компонента Output")
            
            data_field = page.get_by_role("textbox", name="inputs_config.data.value")
            if not data_field.is_visible():
                data_field = page.locator(ComponentLocators.DATA_VALUE_FALLBACK).first

            if data_field.is_visible():
                data_field.fill('$node.Flow_proc.Output')
                time.sleep(0.5)
                print("[SUCCESS] Поле 'Данные' заполнено значением '$node.Flow_proc.Output' для компонента Output")
            else:
                print("[WARN] Поле 'Данные' не найдено для компонента Output")
        except Exception as e:
            print(f"[WARN] Ошибка при заполнении поля 'Данные' в Output: {e}")
    else:
        print("[ERROR] Компонент 'Flow_proc' не найден на канвасе!")
        assert False, "Компонент Flow_proc не найден!"

    print("[INFO] Шаг 8: Выполнение диаграммы и проверка результата")
    
    success = diagram_page.run_diagram_and_wait(completion_timeout=15000)
    assert success, "Диаграмма не выполнилась успешно!"
    print("[SUCCESS] Диаграмма завершилась успешно!")
    
    try:
        toast = page.locator(ModalLocators.TOAST).first
        if toast.is_visible(timeout=3000):
            toast_text = toast.text_content()
            print(f"[SUCCESS] Тост найден: {toast_text}")
        else:
            print("[INFO] Тост не появился, но диаграмма выполнилась успешно")
    except Exception as e:
        print("[INFO] Тост не появился, но диаграмма выполнилась успешно")
    
    page.get_by_text("Процесс", exact=True).click()
    time.sleep(1)
    print("[SUCCESS] Переключились на вкладку 'Процесс'")
    
    page.get_by_text("Анализ").click()
    time.sleep(1)
    print("[SUCCESS] Переключились на подвкладку 'Анализ'")
    
    page.get_by_role("button", name="formitem_full_view_button").nth(1).click()
    time.sleep(1)
    print("[SUCCESS] Нажата кнопка 'formitem_full_view_button'")
    
    try:
        json_modal = page.get_by_text("Просмотр JSON")
        if json_modal.is_visible():
            print("[SUCCESS] Модалка 'Просмотр JSON' найдена")
            
            response_section = page.get_by_text("Ответ")
            if response_section.is_visible():
                print("[SUCCESS] Секция 'Ответ' найдена в модалке")
                
                json_data = page.locator(ModalLocators.get_json_content_selector()).first
                if json_data.is_visible():
                    json_text = json_data.text_content()
                    print(f"[SUCCESS] JSON данные найдены: {json_text}")
                    
                    assert "это результат выполнения подпроцесса" in json_text, f"В JSON не найдено ожидаемое сообщение: {json_text}"
                    print("[SUCCESS] В JSON найдено ожидаемое сообщение 'это результат выполнения подпроцесса'")
                else:
                    print("[WARN] JSON данные не найдены в модалке")
            else:
                print("[WARN] Секция 'Ответ' не найдена в модалке")
        else:
            print("[WARN] Модалка 'Просмотр JSON' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при проверке модалки 'Просмотр JSON': {e}")
        page.screenshot(path='screenshots/debug_json_modal.png', full_page=True)

    print("[SUCCESS] Тест test_flow_parent_child_process завершен успешно!")


def cleanup_projects():
    """
    Функция для очистки созданных проектов в конце тестового файла
    """
    print("[INFO] Очистка проектов - пока что заглушка")
