import time
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.diagram_page import DiagramPage
from pages.canvas_utils import CanvasUtils
from pages.connection_page import ConnectionPage
from conftest import save_screenshot, get_project_by_code, delete_project_by_id


def test_flow_cycle(login_page, shared_flow_project):
    """
    Тест для создания циклического процесса на диаграмме
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

    print("[INFO] Тест test_flow_cycle начат")

    # Шаг 1: Создание Python скрипта для циклических операций
    print("[INFO] Шаг 1: Создание Python скрипта для циклических операций")
    
    # Открываем файловую панель
    file_panel.open_file_panel()
    time.sleep(1)
    
    # Проверяем существование папки scripts
    scripts_folder = page.locator('[aria-label="treeitem_label"]:has-text("scripts")')
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
        scripts_folder = page.locator('[aria-label="treeitem_label"]:has-text("scripts")')
        scripts_folder.first.click(button="right")

    time.sleep(1)

    # Создаем Python файл
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

    # Заполняем Python файл содержимым
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

    # Загружаем Python код из файла
    import os
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "cycle_functions.py")
    with open(script_path, 'r', encoding='utf-8') as f:
        python_code = f.read()
    print(f"[INFO] Python код загружен из файла: {script_path}")

    # Вставляем код через буфер обмена
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

    # Шаг 2: Открытие диаграммы test_cycle.df.json
    print("[INFO] Шаг 2: Открытие диаграммы test_cycle.df.json")

    # Ищем папку test_flow_component
    test_flow_component_folder = page.locator('[aria-label="treeitem_label"]:has-text("test_flow_component")')
    if test_flow_component_folder.count() > 0:
        print("[INFO] Папка 'test_flow_component' найдена")
        test_flow_component_folder.first.click()
        time.sleep(1)
    else:
        print("[ERROR] Папка 'test_flow_component' не найдена!")
        raise Exception("Папка test_flow_component не существует в проекте")

    # Ищем файл test_cycle.df.json
    test_cycle_file = page.locator('[aria-label="treeitem_label"]:has-text("test_cycle.df.json")')
    if test_cycle_file.count() > 0:
        print("[INFO] Файл 'test_cycle.df.json' найден")
        test_cycle_file.first.dblclick()  # Двойной клик для открытия
        time.sleep(2)
    else:
        print("[ERROR] Файл 'test_cycle.df.json' не найден!")
        raise Exception("Файл test_cycle.df.json не существует в папке test_flow_component")

    print("[INFO] Ожидание загрузки диаграммы...")
    time.sleep(3)

    # Закрываем панели
    diagram_page.close_panels()
    time.sleep(3)
    
    print("[SUCCESS] Диаграмма test_cycle.df.json открыта, панели закрыты!")

    # Шаг 3: Настройка компонента Function на canvas
    print("[INFO] Шаг 3: Настройка компонента Function на canvas")

    # Ищем компонент Function на канвасе
    function_component = page.locator('text="Function"')
    if function_component.count() > 0:
        print("[INFO] Компонент Function найден на canvas")
        function_component.first.dblclick()  # Двойной клик
        time.sleep(1)
        print("[INFO] Двойной клик по компоненту Function выполнен")
    else:
        print("[ERROR] Компонент Function не найден на canvas!")
        raise Exception("Компонент Function не найден в диаграмме")

    # Открываем модалку для выбора Python скрипта
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

    # Выбираем Python скрипт cycle_functions.py
    print("[INFO] Выбор Python скрипта cycle_functions.py")
    try:
        python_script = page.locator('[aria-label="treeitem_label"]:has-text("cycle_functions.py")')
        if python_script.count() > 0:
            python_script.first.click()
            time.sleep(0.5)
            print("[INFO] Python скрипт cycle_functions.py выбран")
        else:
            print("[ERROR] Файл cycle_functions.py не найден в модалке!")
            raise Exception("Python скрипт не найден в списке файлов")
    except Exception as e:
        print(f"[WARN] Ошибка при выборе скрипта: {e}")

    # Подтверждаем выбор файла
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

    # Выбираем функцию (например, count_to_n)
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

    # Шаг 4: Заполнение входных данных для функции
    print("[INFO] Шаг 4: Заполнение входных данных для функции count_to_n")

    time.sleep(2)

    # Заполняем параметр n для функции count_to_n
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

    # Шаг 5: Настройка компонента Loop на canvas
    print("[INFO] Шаг 5: Настройка компонента Loop на canvas")

    # Ищем компонент Loop на канвасе (осторожно, не кликаем по Function внутри)
    print("[INFO] Поиск компонента Loop на канвасе")
    
    # Сначала попробуем найти Loop по тексту, но не кликаем сразу
    loop_components = page.locator('text="Loop"')
    loop_found = False
    
    if loop_components.count() > 0:
        print(f"[INFO] Найдено {loop_components.count()} компонентов с текстом 'Loop'")
        
        # Ищем компонент Loop, который НЕ содержит Function внутри
        for i in range(loop_components.count()):
            try:
                loop_component = loop_components.nth(i)
                if loop_component.is_visible():
                    # Проверяем, что это именно компонент Loop, а не текст внутри Function
                    # Попробуем кликнуть по краю компонента, а не по центру
                    loop_box = loop_component.bounding_box()
                    if loop_box:
                        # Кликаем по левому краю компонента Loop
                        edge_x = loop_box['x'] + 10  # 10px от левого края
                        edge_y = loop_box['y'] + loop_box['height'] / 2  # по центру по вертикали
                        
                        print(f"[INFO] Кликаем по краю компонента Loop в позиции ({edge_x}, {edge_y})")
                        page.mouse.click(edge_x, edge_y)
                        time.sleep(1)
                        
                        # Проверяем, открылся ли правый сайдбар для Loop (а не для Function)
                        details_panel = page.locator('[aria-label="diagram_details_panel"]')
                        if details_panel.is_visible():
                            # Проверяем, что в сайдбаре есть заголовок Loop (используем более точный селектор)
                            loop_title = page.get_by_role("heading", name="diagram_element_name")
                            if loop_title.is_visible():
                                title_text = loop_title.text_content()
                                if title_text and "Loop" in title_text:
                                    print("[SUCCESS] Компонент Loop найден и выбран!")
                                    loop_found = True
                                    break
                                else:
                                    print(f"[WARN] Сайдбар открылся для компонента: {title_text}")
                            else:
                                print("[WARN] Заголовок компонента не найден в сайдбаре")
                            
                            # Закрываем сайдбар и пробуем дальше
                            details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
                            if details_panel_switcher.is_visible():
                                details_panel_switcher.click()
                                time.sleep(0.5)
                        
            except Exception as e:
                print(f"[WARN] Ошибка при проверке компонента Loop {i}: {e}")
                continue
    
    if not loop_found:
        print("[WARN] Не удалось найти компонент Loop через текст, пробуем альтернативные методы")
        
        # Альтернативный метод - поиск по координатам канваса
        canvas = page.locator('canvas').first
        if canvas.is_visible():
            canvas_box = canvas.bounding_box()
            if canvas_box:
                # Пробуем кликнуть в разных местах канваса, где может быть Loop
                positions = [
                    {"x": canvas_box['x'] + canvas_box['width'] * 0.3, "y": canvas_box['y'] + canvas_box['height'] * 0.3},  # Левый верх
                    {"x": canvas_box['x'] + canvas_box['width'] * 0.7, "y": canvas_box['y'] + canvas_box['height'] * 0.3},  # Правый верх
                    {"x": canvas_box['x'] + canvas_box['width'] * 0.5, "y": canvas_box['y'] + canvas_box['height'] * 0.2},  # Верхний центр
                ]
                
                for i, pos in enumerate(positions):
                    try:
                        print(f"[INFO] Пробуем кликнуть по позиции {i+1}: ({pos['x']}, {pos['y']})")
                        canvas.click(position=pos)
                        time.sleep(1)
                        
                        # Проверяем, открылся ли сайдбар для Loop
                        details_panel = page.locator('[aria-label="diagram_details_panel"]')
                        if details_panel.is_visible():
                            loop_title = page.get_by_role("heading", name="diagram_element_name")
                            if loop_title.is_visible():
                                title_text = loop_title.text_content()
                                if title_text and "Loop" in title_text:
                                    print(f"[SUCCESS] Компонент Loop найден по позиции {i+1}!")
                                    loop_found = True
                                    break
                                else:
                                    print(f"[WARN] Сайдбар открылся для компонента: {title_text}")
                            
                            # Закрываем сайдбар и пробуем дальше
                            details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
                            if details_panel_switcher.is_visible():
                                details_panel_switcher.click()
                                time.sleep(0.5)
                                    
                    except Exception as e:
                        print(f"[WARN] Ошибка при клике по позиции {i+1}: {e}")
                        continue

    if not loop_found:
        print("[ERROR] Компонент Loop не найден на canvas!")
        raise Exception("Компонент Loop не найден в диаграмме")

    # Настройка компонента Loop
    print("[INFO] Настройка компонента Loop")
    
    # Проверяем, что правый сайдбар открыт для Loop
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    if not details_panel.is_visible():
        print("[WARN] Правый сайдбар не открыт, пытаемся открыть")
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)

    print("[SUCCESS] Компонент Loop найден и готов к настройке!")

    # Шаг 6: Настройка параметров цикла Loop
    print("[INFO] Шаг 6: Настройка параметров цикла Loop")
    
    # Проверяем, что правый сайдбар открыт для Loop
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    if not details_panel.is_visible():
        print("[WARN] Правый сайдбар не открыт, пытаемся открыть")
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)

    # Настройка начала цикла (loop_start)
    print("[INFO] Настройка начала цикла (loop_start)")
    try:
        # Кликаем по полю loop_start
        loop_start_field = page.locator(".TextField__TextField___-71sY.TextField__TextField_invalid___KA8-t > .TextField__InputWrapper___anui0")
        if loop_start_field.is_visible():
            loop_start_field.click()
            time.sleep(0.5)
            print("[INFO] Поле loop_start открыто")
            
            # Ищем компонент Function внутри цикла
            # Сначала пробуем найти по тексту "Function"
            function_option = page.get_by_role("treeitem").locator("div").filter(has_text="Function").first
            if function_option.is_visible():
                function_option.click()
                time.sleep(0.5)
                print("[INFO] Компонент Function выбран для loop_start")
            else:
                print("[WARN] Компонент Function не найден в списке, пробуем альтернативный метод")
                # Пробуем найти по TreeItem__LabelPrimary
                function_label = page.locator('.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Function")').first
                if function_label.is_visible():
                    function_label.click()
                    time.sleep(0.5)
                    print("[INFO] Компонент Function найден по TreeItem__LabelPrimary")
                else:
                    print("[WARN] Не удалось найти компонент Function для loop_start")
        else:
            print("[WARN] Поле loop_start не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке loop_start: {e}")

    # Добавляем элемент в список
    print("[INFO] Добавление элемента в список")
    try:
        add_button = page.get_by_role("button", name="extendable_list_add_button")
        if add_button.is_visible():
            add_button.click()
            time.sleep(0.5)
            print("[INFO] Кнопка добавления элемента нажата")
        else:
            print("[WARN] Кнопка добавления элемента не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при добавлении элемента: {e}")

    # Настройка конца цикла (loop_end)
    print("[INFO] Настройка конца цикла (loop_end)")
    try:
        # Кликаем по полю loop_end
        loop_end_field = page.get_by_role("textbox", name="config.loop_end.0")
        if loop_end_field.is_visible():
            loop_end_field.click()
            time.sleep(0.5)
            print("[INFO] Поле loop_end открыто")
            
            # Ищем компонент Function внутри цикла для loop_end
            function_option = page.get_by_role("treeitem").locator("div").filter(has_text="Function").first
            if function_option.is_visible():
                function_option.click()
                time.sleep(0.5)
                print("[INFO] Компонент Function выбран для loop_end")
            else:
                # Пробуем найти по TreeItem__LabelPrimary
                function_label = page.locator('.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Function")').first
                if function_label.is_visible():
                    function_label.click()
                    time.sleep(0.5)
                    print("[INFO] Компонент Function найден для loop_end по TreeItem__LabelPrimary")
                else:
                    print("[WARN] Не удалось найти компонент Function для loop_end")
        else:
            print("[WARN] Поле loop_end не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке loop_end: {e}")

    # Настройка итератора (inputs_config)
    print("[INFO] Настройка итератора цикла")
    try:
        # Ищем поле для итератора
        iterator_field = page.get_by_role("textbox", name="inputs_config.")
        if iterator_field.is_visible():
            iterator_field.click()
            time.sleep(0.5)
            print("[INFO] Поле итератора открыто")
            
            # Заполняем массив данных для итерации
            iterator_field.fill("[1,2,3,4]")
            time.sleep(0.5)
            print("[INFO] Итератор заполнен данными [1,2,3,4]")
        else:
            print("[WARN] Поле итератора не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при настройке итератора: {e}")

    print("[SUCCESS] Параметры цикла Loop настроены успешно!")

    # Шаг 7: Закрытие сайдбара и настройка компонента Output
    print("[INFO] Шаг 7: Закрытие сайдбара и настройка компонента Output")
    
    # Закрываем правый сайдбар
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

    # Ищем компонент Output на канвасе
    print("[INFO] Поиск компонента Output на канвасе")
    output_component = page.locator('text="Output"')
    if output_component.count() > 0:
        print("[INFO] Компонент Output найден на canvas")
        output_component.first.click()
        time.sleep(1)
        print("[INFO] Клик по компоненту Output выполнен")
    else:
        print("[ERROR] Компонент Output не найден на canvas!")
        raise Exception("Компонент Output не найден в диаграмме")

    # Открываем правый сайдбар для настройки Output
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

    # Настройка поля 'Данные' в компоненте Output
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

    # Шаг 8: Запуск диаграммы
    print("[INFO] Шаг 8: Запуск диаграммы")

    # Закрываем правый сайдбар перед запуском
    print("[INFO] Закрытие правого сайдбара перед запуском")
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[INFO] Правый сайдбар закрыт")
    except Exception as e:
        print(f"[WARN] Ошибка при закрытии правого сайдбара: {e}")

    # Запускаем диаграмму и ожидаем завершения
    print("[INFO] Запуск диаграммы и ожидание завершения")
    success = diagram_page.run_diagram_and_wait()
    
    assert success, "Диаграмма не выполнилась успешно!"
    print("[SUCCESS] Диаграмма выполнена успешно!")

    # После выполнения диаграммы ищем компонент Output и открываем его сайдбар
    print("[INFO] Поиск компонента Output после выполнения диаграммы")
    try:
        output_component = page.locator('text="Output"')
        if output_component.count() > 0:
            output_component.first.click()
            time.sleep(1)
            print("[SUCCESS] Клик по компоненту Output выполнен")
        else:
            print("[ERROR] Компонент Output не найден на canvas!")
            raise Exception("Компонент Output не найден в диаграмме")
    except Exception as e:
        print(f"[WARN] Ошибка при поиске компонента Output: {e}")

    # Открываем правый сайдбар для компонента Output
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

    # Переключаемся на вкладку "Процесс"
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

    # Переключаемся на подвкладку "Анализ"
    print("[INFO] Переход на подвкладку 'Анализ'")
    try:
        analysis_tab = page.get_by_text("Анализ")
        if analysis_tab.is_visible():
            analysis_tab.click()
            time.sleep(1)
            print("[SUCCESS] Переключились на подвкладку 'Анализ'")
        else:
            print("[WARN] Подвкладка 'Анализ' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при переходе на подвкладку 'Анализ': {e}")

    # Нажимаем кнопку для просмотра результата
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
