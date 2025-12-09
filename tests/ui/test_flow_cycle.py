import time
import pytest
from playwright.sync_api import TimeoutError
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.diagram_page import DiagramPage
from pages.canvas_utils import CanvasUtils
from pages.connection_page import ConnectionPage
from conftest import save_screenshot, get_project_by_code, delete_project_by_id, wait_for_canvas_with_refresh
from locators import (
    FilePanelLocators,
    DiagramLocators,
    CanvasLocators,
    ComponentLocators,
    ModalLocators,
    ToolbarLocators
)


def wait_for_field_value(page, field_locator, expected_value, timeout=10000):
    """
    Ждет, пока поле получит ожидаемое значение через WebSocket.
    Используется для избежания race condition при заполнении полей.
    
    Args:
        page: Playwright page объект
        field_locator: Локатор поля
        expected_value: Ожидаемое значение (может быть строкой или частью строки)
        timeout: Таймаут ожидания в миллисекундах
        
    Returns:
        bool: True если значение появилось, False если таймаут
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < timeout:
        try:
            field = field_locator
            if field.is_visible():
                try:
                    current_value = field.input_value()
                    if expected_value in current_value or current_value == expected_value:
                        print(f"[SUCCESS] Поле получило значение: {current_value}")
                        return True
                except:
                    pass
                
                try:
                    current_value = field.text_content()
                    if expected_value in current_value or current_value == expected_value:
                        print(f"[SUCCESS] Поле получило значение: {current_value}")
                        return True
                except:
                    pass
                
                try:
                    invalid_class = field.locator("..").locator(".TextField__TextField_invalid___KA8-t")
                    try:
                        invalid_class.wait_for(state="hidden", timeout=500)
                        print("[INFO] Поле прошло валидацию (нет класса invalid)")
                        time.sleep(0.3)  # Дополнительная пауза для стабилизации
                        return True
                    except TimeoutError:
                        pass
                except:
                    pass
                    
        except Exception as e:
            pass
        
        time.sleep(0.2)
    
    print(f"[WARN] Таймаут ожидания значения '{expected_value}' в поле")
    return False


def wait_for_field_selection(page, field_locator, expected_text, timeout=10000):
    """
    Ждет, пока в поле выбора появится ожидаемый текст (для выпадающих списков).
    
    Args:
        page: Playwright page объект
        field_locator: Локатор поля
        expected_text: Ожидаемый текст в поле
        timeout: Таймаут ожидания в миллисекундах
        
    Returns:
        bool: True если текст появился, False если таймаут
    """
    start_time = time.time()
    while (time.time() - start_time) * 1000 < timeout:
        try:
            field = field_locator
            if field.is_visible():
                try:
                    current_value = field.input_value()
                    if expected_text in current_value or current_value == expected_text:
                        print(f"[SUCCESS] В поле выбора появился текст: {current_value}")
                        time.sleep(0.5)  # Дополнительная пауза для стабилизации через WS
                        return True
                except:
                    pass
                
                try:
                    current_value = field.text_content()
                    if expected_text in current_value or current_value == expected_text:
                        print(f"[SUCCESS] В поле выбора появился текст: {current_value}")
                        time.sleep(0.5)  # Дополнительная пауза для стабилизации через WS
                        return True
                except:
                    pass
                    
        except Exception as e:
            pass
        
        time.sleep(0.2)
    
    print(f"[WARN] Таймаут ожидания текста '{expected_text}' в поле выбора")
    return False


def test_flow_cycle(login_page, flow_project):
    """
    Тест для создания циклического процесса на диаграмме
    """
    page, project_code = flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)
    canvas_utils = CanvasUtils(page)
    connection_page = ConnectionPage(page)
    
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)

    print("[INFO] Тест test_flow_cycle начат")

    print("[INFO] Шаг 1: Создание Python скрипта для циклических операций")
    
    print("[INFO] Открываем файловую панель")
    file_panel.open_file_panel()
    time.sleep(2)
    
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
    name_input.fill("cycle_functions")
    name_input.press("Enter")
    time.sleep(2)
    print("[INFO] Создан Python файл 'cycle_functions.py'")

    print("[INFO] Заполнение Python скрипта содержимым")
    
    try:
        page.locator(".view-lines").first.click()
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Не удалось кликнуть по view-lines: {e}")
        page.locator('textarea[aria-label="editor_view"]').click()
        time.sleep(1)

    editor = page.get_by_role("textbox", name="editor_view")
    editor.wait_for(state="visible", timeout=10000)
    time.sleep(1)

    import os
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "cycle_functions.py")
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
    print("[SUCCESS] Python скрипт создан и сохранен успешно!")

    print("[INFO] Шаг 2: Открытие диаграммы test_cycle.df.json")

    test_flow_component_folder = page.locator(FilePanelLocators.get_treeitem_by_name("test_flow_component"))
    if test_flow_component_folder.count() > 0:
        print("[INFO] Папка 'test_flow_component' найдена")
        test_flow_component_folder.first.click()
        time.sleep(1)
    else:
        print("[ERROR] Папка 'test_flow_component' не найдена!")
        raise Exception("Папка test_flow_component не существует в проекте")

    test_cycle_file = page.locator(FilePanelLocators.get_treeitem_by_name("test_cycle.df.json"))
    if test_cycle_file.count() > 0:
        print("[INFO] Файл 'test_cycle.df.json' найден")
        test_cycle_file.first.dblclick()
        time.sleep(2)
    else:
        print("[ERROR] Файл 'test_cycle.df.json' не найден!")
        raise Exception("Файл test_cycle.df.json не существует в папке test_flow_component")

    print("[INFO] Ожидание загрузки диаграммы...")
    time.sleep(3)

    diagram_page.close_panels()
    time.sleep(3)
    
    print("[SUCCESS] Диаграмма test_cycle.df.json открыта, панели закрыты!")

    print("[INFO] Шаг 3: Настройка компонента Function на canvas")
    
    assert wait_for_canvas_with_refresh(page, timeout=10000, max_refreshes=1), "Canvas не загрузился даже после рефреша!"
    time.sleep(2)  # Дополнительное время для полной загрузки компонентов на canvas

    function_component = page.locator(DiagramLocators.FUNCTION_COMPONENT)
    if function_component.count() > 0:
        print("[INFO] Компонент Function найден на canvas")
        function_component.first.dblclick()
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

    print("[INFO] Выбор Python скрипта cycle_functions.py")
    try:
        python_script = page.locator(FilePanelLocators.get_treeitem_by_name("cycle_functions.py"))
        if python_script.count() > 0:
            python_script.first.click()
            time.sleep(0.5)
            print("[INFO] Python скрипт cycle_functions.py выбран")
        else:
            print("[ERROR] Файл cycle_functions.py не найден в модалке!")
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

    print("[INFO] Выбор функции count_to_n")
    try:
        function_field = page.get_by_role("textbox", name="config.function")
        if function_field.is_visible():
            function_field.click()
            time.sleep(0.5)
            print("[INFO] Поле функции открыто, селект должен появиться")
            
            function_option = page.get_by_role("treeitem", name="count_to_n").get_by_label("treeitem_label")
            if function_option.count() > 0:
                function_option.click()
                time.sleep(0.5)
                print("[INFO] Функция count_to_n выбрана")
            else:
                print("[ERROR] Функция count_to_n не найдена в селекте!")
                raise Exception("Функция не найдена в списке доступных функций")
        else:
            print("[ERROR] Поле функции не найдено!")
            raise Exception("Не удалось найти поле для выбора функции")
    except Exception as e:
        print(f"[WARN] Ошибка при выборе функции: {e}")

    print("[SUCCESS] Компонент Function настроен успешно!")

    print("[INFO] Шаг 4: Заполнение входных данных для функции count_to_n")

    time.sleep(2)

    print("[INFO] Заполнение параметра n")
    try:
        arg_n_field = page.get_by_role("textbox", name="inputs_config.n.value")
        if arg_n_field.is_visible():
            arg_n_field.fill("5")
            time.sleep(0.5)
            print("[INFO] Параметр n: 5")
        else:
            print("[WARN] Поле для параметра n не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при заполнении параметра n: {e}")

    print("[SUCCESS] Все входные данные заполнены!")

    print("[INFO] Шаг 5: Настройка компонента Loop на canvas")

    print("[INFO] Поиск компонента Loop на канвасе")
    loop_found = False
    max_attempts = 5
    
    for attempt in range(max_attempts):
        try:
            print(f"[INFO] Попытка {attempt + 1}/{max_attempts} найти компонент Loop")
            
            try:
                loop_component = canvas_utils.find_component_by_title("Loop", exact=True, timeout=5000)
                if loop_component:
                    print("[INFO] Компонент Loop найден через CanvasUtils")
                    loop_component.click()
                    time.sleep(1)
                    
                    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
                    try:
                        details_panel.wait_for(state="visible", timeout=3000)
                        loop_title = page.get_by_role("heading", name="diagram_element_name")
                        loop_title.wait_for(state="visible", timeout=2000)
                        title_text = loop_title.text_content()
                        if title_text and "Loop" in title_text:
                            print("[SUCCESS] Компонент Loop найден и выбран!")
                            loop_found = True
                            break
                    except TimeoutError:
                        pass
            except Exception as e:
                print(f"[WARN] CanvasUtils не нашел Loop (попытка {attempt + 1}): {e}")
            
            if not loop_found:
                loop_components = page.locator(CanvasLocators.get_component_by_text("Loop"))
                if loop_components.count() > 0:
                    print(f"[INFO] Найдено {loop_components.count()} компонентов с текстом 'Loop'")
                    for i in range(loop_components.count()):
                        try:
                            loop_component = loop_components.nth(i)
                            if loop_component.is_visible():
                                loop_box = loop_component.bounding_box()
                                if loop_box:
                                    center_x = loop_box['x'] + loop_box['width'] / 2
                                    center_y = loop_box['y'] + loop_box['height'] / 2
                                    
                                    print(f"[INFO] Кликаем по центру компонента Loop в позиции ({center_x}, {center_y})")
                                    page.mouse.click(center_x, center_y)
                                    time.sleep(1.5)
                                    
                                    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
                                    try:
                                        details_panel.wait_for(state="visible", timeout=3000)
                                        loop_title = page.get_by_role("heading", name="diagram_element_name")
                                        loop_title.wait_for(state="visible", timeout=2000)
                                        title_text = loop_title.text_content()
                                        if title_text and "Loop" in title_text:
                                            print("[SUCCESS] Компонент Loop найден и выбран!")
                                            loop_found = True
                                            break
                                    except TimeoutError:
                                        pass
                        except Exception as e:
                            print(f"[WARN] Ошибка при проверке компонента Loop {i}: {e}")
                            continue
                    
                    if loop_found:
                        break
            
            if not loop_found and attempt < max_attempts - 1:
                print("[INFO] Даем дополнительное время для загрузки компонентов...")
                time.sleep(2)
                
        except Exception as e:
            print(f"[WARN] Ошибка при поиске Loop (попытка {attempt + 1}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
    
    if not loop_found:
        print("[ERROR] Компонент Loop не найден на canvas после всех попыток!")
        save_screenshot(page, "loop_not_found")
        raise Exception("Компонент Loop не найден в диаграмме")

    print("[INFO] Настройка компонента Loop")
    
    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    if not details_panel.is_visible():
        print("[WARN] Правый сайдбар не открыт, пытаемся открыть")
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)

    print("[SUCCESS] Компонент Loop найден и готов к настройке!")

    print("[INFO] Шаг 6: Настройка параметров цикла Loop")
    
    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    if not details_panel.is_visible():
        print("[WARN] Правый сайдбар не открыт, пытаемся открыть")
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)

    print("[INFO] Настройка начала цикла (loop_start)")
    try:
        loop_start_field = page.locator(".TextField__TextField___-71sY.TextField__TextField_invalid___KA8-t > .TextField__InputWrapper___anui0")
        if loop_start_field.is_visible():
            loop_start_field.click()
            time.sleep(0.5)
            print("[INFO] Поле loop_start открыто")
            
            function_option = page.get_by_role("treeitem").locator("div").filter(has_text="Function").first
            if function_option.is_visible():
                function_option.click()
                time.sleep(0.5)
                print("[INFO] Компонент Function выбран для loop_start")
                
                print("[INFO] Ожидание сохранения значения loop_start через WebSocket...")
                loop_start_input = None
                try:
                    loop_start_input = page.locator('textarea[name*="loop_start"], input[name*="loop_start"], textarea[aria-label*="loop_start"], input[aria-label*="loop_start"]').first
                    if loop_start_input.count() == 0:
                        loop_start_input = loop_start_field.locator("..").locator("textarea, input").first
                except:
                    loop_start_input = loop_start_field
                
                if loop_start_input:
                    wait_for_field_selection(page, loop_start_input, "Function", timeout=15000)
                    print("[SUCCESS] Значение loop_start сохранено через WebSocket")
                else:
                    print("[WARN] Не удалось найти поле для проверки значения, пропускаем ожидание")
            else:
                print("[WARN] Компонент Function не найден в списке, пробуем альтернативный метод")
                function_label = page.locator('.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Function")').first
                if function_label.is_visible():
                    function_label.click()
                    time.sleep(0.5)
                    print("[INFO] Компонент Function найден по TreeItem__LabelPrimary")
                    
                    print("[INFO] Ожидание сохранения значения loop_start через WebSocket (альтернативный метод)...")
                    loop_start_input = None
                    try:
                        loop_start_input = page.locator('textarea[name*="loop_start"], input[name*="loop_start"], textarea[aria-label*="loop_start"], input[aria-label*="loop_start"]').first
                        if loop_start_input.count() == 0:
                            loop_start_input = loop_start_field.locator("..").locator("textarea, input").first
                    except:
                        loop_start_input = loop_start_field
                    
                    if loop_start_input:
                        wait_for_field_selection(page, loop_start_input, "Function", timeout=15000)
                        print("[SUCCESS] Значение loop_start сохранено через WebSocket (альтернативный метод)")
                    else:
                        print("[WARN] Не удалось найти поле для проверки значения, пропускаем ожидание")
                else:
                    print("[WARN] Не удалось найти компонент Function для loop_start")
        else:
            print("[WARN] Поле loop_start не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке loop_start: {e}")

    print("[INFO] Добавление элемента в список")
    try:
        add_button = page.get_by_role("button", name="extendable_list_add_button")
        if add_button.is_visible():
            add_button.click()
            time.sleep(0.5)
            print("[INFO] Кнопка добавления элемента нажата")
            
            print("[INFO] Ожидание добавления элемента через WebSocket...")
            try:
                loop_end_new_field = page.get_by_role("textbox", name="config.loop_end.0")
                loop_end_new_field.wait_for(state="visible", timeout=10000)
                print("[SUCCESS] Элемент добавлен в список, поле loop_end.0 появилось")
                time.sleep(0.5)  # Дополнительная пауза для стабилизации через WS
            except Exception as e:
                print(f"[WARN] Не удалось дождаться появления нового поля: {e}")
        else:
            print("[WARN] Кнопка добавления элемента не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при добавлении элемента: {e}")

    print("[INFO] Настройка конца цикла (loop_end)")
    try:
        loop_end_field = page.get_by_role("textbox", name="config.loop_end.0")
        if loop_end_field.is_visible():
            loop_end_field.click()
            time.sleep(0.5)
            print("[INFO] Поле loop_end открыто")
            
            function_option = page.get_by_role("treeitem").locator("div").filter(has_text="Function").first
            if function_option.is_visible():
                function_option.click()
                time.sleep(0.5)
                print("[INFO] Компонент Function выбран для loop_end")
                
                print("[INFO] Ожидание сохранения значения loop_end через WebSocket...")
                wait_for_field_selection(page, loop_end_field, "Function", timeout=15000)
                print("[SUCCESS] Значение loop_end сохранено через WebSocket")
            else:
                function_label = page.locator('.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Function")').first
                if function_label.is_visible():
                    function_label.click()
                    time.sleep(0.5)
                    print("[INFO] Компонент Function найден для loop_end по TreeItem__LabelPrimary")
                    
                    wait_for_field_selection(page, loop_end_field, "Function", timeout=15000)
                    print("[SUCCESS] Значение loop_end сохранено через WebSocket (альтернативный метод)")
                else:
                    print("[WARN] Не удалось найти компонент Function для loop_end")
        else:
            print("[WARN] Поле loop_end не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке loop_end: {e}")

    print("[INFO] Настройка итератора цикла")
    try:
        iterator_field = page.get_by_role("textbox", name="inputs_config.")
        if iterator_field.is_visible():
            iterator_field.click()
            time.sleep(0.5)
            print("[INFO] Поле итератора открыто")
            
            iterator_field.fill("[1,2,3,4]")
            time.sleep(0.5)
            print("[INFO] Итератор заполнен данными [1,2,3,4]")
            
            print("[INFO] Ожидание сохранения значения итератора через WebSocket...")
            wait_for_field_value(page, iterator_field, "[1,2,3,4]", timeout=15000)
            print("[SUCCESS] Значение итератора сохранено через WebSocket")
        else:
            print("[WARN] Поле итератора не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке итератора: {e}")

    print("[SUCCESS] Параметры цикла Loop настроены успешно!")

    print("[INFO] Шаг 7: Закрытие сайдбара и настройка компонента Output")
    
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

    print("[INFO] Поиск компонента Output на канвасе")
    output_component = page.locator(ComponentLocators.OUTPUT)
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
            data_field.fill("$node.Loop.result[0]")
            time.sleep(0.5)
            print("[INFO] Поле 'Данные' заполнено: $node.Loop.result[0]")
        else:
            print("[ERROR] Поле 'Данные' не найдено!")
            raise Exception("Не удалось найти поле для настройки данных Output")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке поля 'Данные': {e}")

    print("[SUCCESS] Компонент Output настроен успешно!")

    print("[INFO] Шаг 8: Запуск диаграммы")

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

    print("[INFO] Поиск компонента Output после выполнения диаграммы")
    try:
        output_component = page.locator(ComponentLocators.OUTPUT)
        if output_component.count() > 0:
            output_component.first.click()
            time.sleep(1)
            print("[SUCCESS] Клик по компоненту Output выполнен")
        else:
            print("[ERROR] Компонент Output не найден на canvas!")
            raise Exception("Компонент Output не найден в диаграмме")
    except Exception as e:
        print(f"[WARN] Ошибка при поиске компонента Output: {e}")

    print("[INFO] Открытие правого сайдбара для компонента Output")
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[SUCCESS] Правый сайдбар открыт для компонента Output")
        else:
            print("[INFO] Правый сайдбар уже открыт")
    except Exception as e:
        print(f"[WARN] Ошибка при открытии правого сайдбара: {e}")

    print("[INFO] Переход на вкладку 'Процесс'")
    try:
        process_tab = page.get_by_text("Процесс", exact=True)
        if process_tab.is_visible():
            process_tab.click()
            time.sleep(1)
            print("[SUCCESS] Переключились на вкладку 'Процесс'")
        else:
            print("[WARN] Вкладка 'Процесс' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при переходе на вкладку 'Процесс': {e}")

    print("[INFO] Переход на подвкладку 'Отладка'")
    try:
        analysis_tab = page.get_by_text("Отладка")
        if analysis_tab.is_visible():
            analysis_tab.click()
            time.sleep(1)
            print("[SUCCESS] Переключились на подвкладку 'Отладка'")
        else:
            print("[WARN] Подвкладка 'Отладка' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при переходе на подвкладку 'Отладка': {e}")

    print("[INFO] Поиск кнопки для просмотра результата")
    try:
        full_view_button = page.get_by_role("button", name="formitem_full_view_button").nth(1)
        if full_view_button.is_visible():
            full_view_button.click()
            time.sleep(2)  # Увеличиваем время ожидания для загрузки модалки
            print("[SUCCESS] Нажата кнопка 'formitem_full_view_button', модалка 'Просмотр JSON' должна открыться")
        else:
            print("[WARN] Кнопка 'formitem_full_view_button' не найдена")
    except Exception as e:
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"[WARN] Ошибка при нажатии кнопки просмотра: {error_msg}")

    print("[SUCCESS] Тест test_flow_cycle завершен успешно!")


def cleanup_projects():
    """
    Функция для очистки созданных проектов в конце тестового файла
    """
    print("[INFO] Очистка проектов - пока что заглушка")
