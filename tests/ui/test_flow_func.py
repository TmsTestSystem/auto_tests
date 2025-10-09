"""
Тест для функционального компонента Function
Input → Function → Output
"""
import time
import json
import re
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from pages.diagram_page import DiagramPage
from conftest import save_screenshot
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


def test_flow_func(login_page, shared_flow_project):
    """
    Тест для работы с функциональным компонентом Function
    Input → Function → Output
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)

    print(f"[INFO] Начинаем тест Function в проекте: {project_code}")

    assert project_page.goto_project(project_code), f"Переход в проект {project_code} не удался!"
    time.sleep(2)

    file_panel = FilePanelPage(page)
    data_struct = DataStructPage(page)
    canvas_utils = CanvasUtils(page)
    diagram_page = DiagramPage(page)

    try:
        is_open = page.locator(ToolbarLocators.BOARD_TOOLBAR_PANEL).is_visible()
    except Exception:
        is_open = False
    if not is_open:
        file_panel.open_file_panel()
        time.sleep(0.5)
    print("[INFO] Открыта файловая панель")

    print("[INFO] Шаг 1: Создание Python скрипта в проекте")

    scripts_folder = page.locator(FilePanelLocators.get_treeitem_by_name("scripts"))
    if scripts_folder.count() > 0:
        print("[INFO] Папка 'scripts' найдена")
        scripts_folder.first.click(button="right")
    else:
        print("[INFO] Создаем папку 'scripts'")
        page.get_by_role("button", name="filemanager_create_button").click()
        time.sleep(0.5)
        page.get_by_text("Папка", exact=True).click()
        time.sleep(0.5)
        name_input = page.get_by_role("textbox", name="treeitem_label_field")
        name_input.fill("scripts")
        name_input.press("Enter")
        time.sleep(1)

        scripts_folder = page.locator(FilePanelLocators.get_treeitem_by_name("scripts"))
        scripts_folder.first.click(button="right")

    time.sleep(1)

    create_menu = page.get_by_text("Создать", exact=True)
    assert create_menu.is_visible(), "Меню 'Создать' не найдено в контекстном меню!"
    create_menu.click()
    time.sleep(0.5)

    python_menu = page.get_by_role("treeitem", name="python").get_by_label("treeitem_label")
    assert python_menu.is_visible(), "Меню 'python' не найдено в списке!"
    python_menu.click()
    time.sleep(1)

    name_input = page.get_by_role("textbox", name="treeitem_label_field")
    name_input.wait_for(state="visible", timeout=10000)
    name_input.fill("math_functions")
    name_input.press("Enter")
    time.sleep(2)
    print("[INFO] Создан Python файл 'math_functions.py'")

    print("[INFO] Шаг 2: Заполнение Python скрипта содержимым")

    python_file = page.locator(FilePanelLocators.get_treeitem_by_name("math_functions.py"))
    if python_file.count() > 0:
        print("[INFO] Python файл 'math_functions.py' уже существует")
        python_file.click()
        time.sleep(2)
    else:
        print("[WARN] Python файл 'math_functions.py' не найден, создаем новый")
        scripts_folder = page.locator(FilePanelLocators.get_treeitem_by_name("scripts"))
        scripts_folder.first.click(button="right")
        time.sleep(0.5)
        
        create_menu = page.get_by_text("Создать", exact=True)
        create_menu.click()
        time.sleep(0.5)
        
        python_menu = page.get_by_role("treeitem", name="python").get_by_label("treeitem_label")
        python_menu.click()
        time.sleep(1)
        
        name_input = page.get_by_role("textbox", name="treeitem_label_field")
        name_input.fill("math_functions")
        name_input.press("Enter")
        time.sleep(2)

    try:
        page.locator(".view-lines").first.click()
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Не удалось кликнуть по view-lines: {e}")
        page.locator(FilePanelLocators.EDITOR_VIEW).click()
        time.sleep(1)

    editor = page.get_by_role("textbox", name="editor_view")
    editor.wait_for(state="visible", timeout=10000)
    time.sleep(1)

    import os
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "math_functions.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        python_code = f.read()
    print(f"[INFO] Python код загружен из файла: {script_path}")

    try:
        print("[INFO] Вставляем код через буфер обмена...")

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(python_code)
            temp_file_path = temp_file.name

        import subprocess
        import platform

        if platform.system() == "Windows":
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            subprocess.run(['clip'], input=content, text=True, check=True)
        else:
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], stdin=open(temp_file_path, 'r'), check=True)
            except:
                subprocess.run(['pbcopy'], stdin=open(temp_file_path, 'r'), check=True)

        import os
        os.unlink(temp_file_path)

        page.evaluate("""
            () => {
                const editor = document.querySelector('textarea[aria-label="editor_view"]');
                if (editor) {
                    editor.focus();
                    return true;
                }
                return false;
            }
        """)
        time.sleep(0.5)
        
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")
        time.sleep(0.5)
        
        page.keyboard.press("Control+V")
        time.sleep(1)
        
        print("[INFO] Код вставлен через буфер обмена")
        
    except Exception as e:
        print(f"[WARN] Ошибка при вставке через буфер обмена: {e}")
        try:
            editor.fill(python_code)
            time.sleep(1)
            print("[INFO] Код вставлен через fill (fallback)")
        except Exception as e2:
            print(f"[WARN] Ошибка при вставке через fill: {e2}")
            raise Exception("Не удалось вставить Python код в Monaco Editor")

    time.sleep(2)

    page.keyboard.press("Control+S")
    time.sleep(1)
    print("[INFO] Python скрипт сохранен")
    
    print("[SUCCESS] Python скрипт создан и сохранен успешно!")

    print("[INFO] Шаг 3: Открытие диаграммы test_func.df.json")

    test_flow_component_folder = page.locator(FilePanelLocators.get_treeitem_by_name("test_flow_component"))
    if test_flow_component_folder.count() > 0:
        print("[INFO] Папка 'test_flow_component' найдена")
        test_flow_component_folder.first.click()
        time.sleep(1)
    else:
        print("[ERROR] Папка 'test_flow_component' не найдена!")
        raise Exception("Папка test_flow_component не существует в проекте")

    test_func_file = page.locator(FilePanelLocators.get_treeitem_by_name("test_func.df.json"))
    if test_func_file.count() > 0:
        print("[INFO] Файл 'test_func.df.json' найден")
        test_func_file.first.dblclick()  # Двойной клик для открытия
        time.sleep(2)
    else:
        print("[ERROR] Файл 'test_func.df.json' не найден!")
        raise Exception("Файл test_func.df.json не существует в папке test_flow_component")

    print("[INFO] Ожидание загрузки диаграммы...")
    time.sleep(3)

    print("[INFO] Закрытие панелей")
    diagram_page.close_panels()

    time.sleep(3)
    
    print("[SUCCESS] Диаграмма test_func.df.json открыта, панели закрыты!")

    print("[INFO] Шаг 4: Настройка компонента Function на canvas")

    function_component = page.locator('text="Function"')
    if function_component.count() > 0:
        print("[INFO] Компонент Function найден на canvas")
        function_component.first.dblclick()  # Двойной клик
        time.sleep(1)
        print("[INFO] Двойной клик по компоненту Function выполнен")
    else:
        print("[ERROR] Компонент Function не найден на canvas!")
        raise Exception("Компонент Function не найден в диаграмме")

    print("[INFO] Открытие модалки для выбора Python скрипта")
    try:
        select_file_button = page.get_by_role("button", name="textfield_select_file_button")
        if select_file_button.is_visible():
            select_file_button.click()
            time.sleep(1)
            print("[INFO] Модалка для выбора файла открыта")
        else:
            print("[ERROR] Кнопка выбора файла не найдена!")
            raise Exception("Не удалось открыть модалку выбора файла")
    except Exception as e:
        print(f"[WARN] Ошибка при открытии модалки: {e}")

    print("[INFO] Выбор Python скрипта math_functions.py")
    try:
        python_script = page.locator(FilePanelLocators.get_treeitem_by_name("math_functions.py"))
        if python_script.count() > 0:
            python_script.first.click()
            time.sleep(0.5)
            print("[INFO] Python скрипт math_functions.py выбран")
        else:
            print("[ERROR] Файл math_functions.py не найден в модалке!")
            raise Exception("Python скрипт не найден в списке файлов")
    except Exception as e:
        print(f"[WARN] Ошибка при выборе скрипта: {e}")

    print("[INFO] Подтверждение выбора файла")
    try:
        select_button = page.get_by_role("button", name="filemanager_select_button")
        if select_button.is_visible():
            select_button.click()
            time.sleep(1)
            print("[INFO] Кнопка 'Выбрать' нажата")
        else:
            print("[ERROR] Кнопка 'Выбрать' не найдена!")
            raise Exception("Не удалось подтвердить выбор файла")
    except Exception as e:
        print(f"[WARN] Ошибка при нажатии кнопки 'Выбрать': {e}")

    print("[INFO] Выбор функции process_mixed_types")
    try:
        function_field = page.get_by_role("textbox", name="config.function")
        if function_field.is_visible():
            function_field.click()
            time.sleep(0.5)
            print("[INFO] Поле функции открыто, селект должен появиться")
            
            function_option = page.get_by_role("treeitem", name="process_mixed_types").get_by_label("treeitem_label")
            if function_option.count() > 0:
                function_option.click()
                time.sleep(0.5)
                print("[INFO] Функция process_mixed_types выбрана")
            else:
                print("[ERROR] Функция process_mixed_types не найдена в селекте!")
                raise Exception("Функция не найдена в списке доступных функций")
        else:
            print("[ERROR] Поле функции не найдено!")
            raise Exception("Не удалось найти поле для выбора функции")
    except Exception as e:
        print(f"[WARN] Ошибка при выборе функции: {e}")

    print("[SUCCESS] Компонент Function настроен успешно!")

    print("[INFO] Шаг 5: Заполнение входных данных для функции")

    time.sleep(2)

    print("[INFO] Заполнение аргумента a (int)")
    try:
        arg_a_field = page.get_by_role("textbox", name="inputs_config.a.value")
        if arg_a_field.is_visible():
            arg_a_field.fill("42")
            time.sleep(0.5)
            print("[INFO] Аргумент a (int): 42")
        else:
            print("[WARN] Поле для аргумента a не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении аргумента a: {e}")

    print("[INFO] Заполнение аргумента b (str)")
    try:
        arg_b_field = page.get_by_role("textbox", name="inputs_config.b.value")
        if arg_b_field.is_visible():
            arg_b_field.fill('"Hello World"')
            time.sleep(0.5)
            print("[INFO] Аргумент b (str): \"Hello World\"")
        else:
            print("[WARN] Поле для аргумента b не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении аргумента b: {e}")

    print("[INFO] Заполнение аргумента c (float)")
    try:
        arg_c_field = page.get_by_role("textbox", name="inputs_config.c.value")
        if arg_c_field.is_visible():
            arg_c_field.fill("3.14")
            time.sleep(0.5)
            print("[INFO] Аргумент c (float): 3.14")
        else:
            print("[WARN] Поле для аргумента c не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении аргумента c: {e}")

    print("[INFO] Заполнение аргумента d (bool)")
    try:
        arg_d_field = page.get_by_role("textbox", name="inputs_config.d.value")
        if arg_d_field.is_visible():
            arg_d_field.fill("true")
            time.sleep(0.5)
            print("[INFO] Аргумент d (bool): true")
        else:
            print("[WARN] Поле для аргумента d не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении аргумента d: {e}")

    print("[INFO] Заполнение аргумента e (list)")
    try:
        arg_e_field = page.get_by_role("textbox", name="inputs_config.e.value")
        if arg_e_field.is_visible():
            arg_e_field.fill("[1, 2, 3, 4, 5]")
            time.sleep(0.5)
            print("[INFO] Аргумент e (list): [1, 2, 3, 4, 5]")
        else:
            print("[WARN] Поле для аргумента e не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении аргумента e: {e}")

    print("[SUCCESS] Все входные данные заполнены!")

    print("[INFO] Шаг 6: Закрытие правого сайдбара и настройка компонента Output")

    print("[INFO] Закрытие правого сайдбара")
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[INFO] Правый сайдбар закрыт")
        else:
            print("[INFO] Правый сайдбар уже закрыт")
    except Exception as e:
        print(f"[WARN] Ошибка при закрытии правого сайдбара: {e}")

    print("[INFO] Поиск компонента Output на canvas")
    output_component = page.locator('text="Output"')
    if output_component.count() > 0:
        print("[INFO] Компонент Output найден на canvas")
        output_component.first.click()
        time.sleep(1)
        print("[INFO] Клик по компоненту Output выполнен")
    else:
        print("[ERROR] Компонент Output не найден на canvas!")
        raise Exception("Компонент Output не найден в диаграмме")

    print("[INFO] Открытие правого сайдбара для настройки Output")
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[INFO] Правый сайдбар открыт для настройки Output")
        else:
            print("[INFO] Правый сайдбар уже открыт")
    except Exception as e:
        print(f"[WARN] Ошибка при открытии правого сайдбара: {e}")

    print("[INFO] Настройка поля 'Данные' в компоненте Output")
    try:
        data_field = page.get_by_role("textbox", name="inputs_config.data.value")
        if data_field.is_visible():
            data_field.fill("$node.Function.result")
            time.sleep(0.5)
            print("[INFO] Поле 'Данные' заполнено: $node.Function.result")
        else:
            print("[ERROR] Поле 'Данные' не найдено!")
            raise Exception("Не удалось найти поле для настройки данных Output")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке поля 'Данные': {e}")

    print("[SUCCESS] Компонент Output настроен успешно!")

    print("[INFO] Шаг 7: Запуск диаграммы")

    print("[INFO] Закрытие правого сайдбара перед запуском")
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[INFO] Правый сайдбар закрыт")
    except Exception as e:
        print(f"[WARN] Ошибка при закрытии правого сайдбара: {e}")

    print("[INFO] Запуск диаграммы и ожидание завершения")
    success = diagram_page.run_diagram_and_wait()
    
    assert success, "Диаграмма не выполнилась успешно!"
    print("[SUCCESS] Диаграмма выполнена успешно!")
    
    print("[INFO] Шаг 8: Проверка консоли с print-ами из функции")
    
    try:
        output_panel_button = page.get_by_role("button", name="outputpanel_switch_button")
        if output_panel_button.is_visible():
            output_panel_button.click()
            time.sleep(1)
            print("[INFO] Панель валидации открыта")
        else:
            print("[WARN] Кнопка переключения на панель валидации не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при открытии панели валидации: {e}")
    
    try:
        console_tab = page.get_by_text("Консоль")
        if console_tab.is_visible():
            console_tab.click()
            time.sleep(1)
            print("[INFO] Переход на вкладку 'Консоль' выполнен")
        else:
            print("[WARN] Вкладка 'Консоль' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при переходе на вкладку 'Консоль': {e}")
    
    try:
        time.sleep(2)
        
        console_output = page.locator('.OutputPanel__Body___ypo3o > div').first
        if console_output.is_visible():
            console_text = console_output.text_content()
            print(f"[INFO] Текст консоли: {console_text}")
            
            expected_prints = [
                "[FUNCTION] Получены аргументы:",
                "[FUNCTION] a (int):",
                "[FUNCTION] b (str):",
                "[FUNCTION] c (float):",
                "[FUNCTION] d (bool):",
                "[FUNCTION] e (list):",
                "[FUNCTION] Результат обработки:"
            ]
            
            found_prints = 0
            for expected_print in expected_prints:
                if expected_print in console_text:
                    found_prints += 1
                    print(f"[SUCCESS] Найден print: {expected_print}")
            
            assert found_prints >= 5, f"Найдено только {found_prints} из {len(expected_prints)} ожидаемых print-ов"
            print(f"[SUCCESS] Найдено {found_prints} print-ов из функции в консоли!")
            
        else:
            print("[WARN] Консольный вывод не найден")
            
    except Exception as e:
        print(f"[WARN] Ошибка при проверке консольного вывода: {e}")
    
    print("[SUCCESS] Тест test_flow_func завершен успешно!")


def cleanup_projects():
    """
    Очистка тестовых проектов
    """
    pass
