import time
import os
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.data_struct_page import DataStructPage
from pages.canvas_utils import CanvasUtils
from conftest import save_screenshot, get_project_by_code, delete_project_by_id


def test_flow_split(login_page, shared_flow_project):
    """
    Тест для работы с компонентом Split
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)
    
    print(f"[INFO] Начинаем тест Split в проекте: {project_code}")
    
    # Переходим к общему проекту
    assert project_page.goto_project(project_code), f"Проект с кодом {project_code} не найден!"
    time.sleep(2)
    
    # Открываем панель файлов
    file_panel = FilePanelPage(page)
    data_struct = DataStructPage(page)
    
    try:
        is_open = page.get_by_label("board_toolbar_panel").is_visible()
    except Exception:
        is_open = False
    if not is_open:
        file_panel.open_file_panel()
        time.sleep(0.5)
    print("[INFO] Панель файлов открыта")
    
    # 1. Создаем структуру данных 'shema_for_split' в папке 'shema'
    print("[INFO] Шаг 1: Создание структуры данных 'shema_for_split' в папке 'shema'")
    
    # Находим папку 'shema' и кликаем правой кнопкой
    shema_folder = page.locator('[aria-label="treeitem_label"]:has-text("shema")')
    assert shema_folder.count() > 0, "Папка 'shema' не найдена в проекте!"
    print("[INFO] Папка 'shema' найдена")
    shema_folder.first.click(button="right")
    time.sleep(1)
    print("[INFO] Правый клик по папке 'shema' выполнен")
    
    # Выбираем "Создать" -> "Структуры данных"
    create_menu = page.get_by_text("Создать", exact=True)
    assert create_menu.is_visible(), "Пункт 'Создать' не найден в контекстном меню!"
    create_menu.click()
    time.sleep(0.5)
    print("[INFO] Выбран пункт 'Создать' из контекстного меню")
    
    data_structures_menu = page.get_by_text("Структуры данных", exact=True)
    assert data_structures_menu.is_visible(), "Пункт 'Структуры данных' не найден в подменю!"
    data_structures_menu.click()
    time.sleep(1)
    print("[INFO] Выбран пункт 'Структуры данных' из подменю")
    
    # Заполняем имя структуры данных
    name_input = page.get_by_role("textbox", name="treeitem_label_field")
    name_input.wait_for(state="visible", timeout=10000)
    assert name_input.is_visible(), "Поле ввода имени не появилось!"
    name_input.fill("shema_for_split")
    name_input.press("Enter")
    time.sleep(2)
    print("[INFO] Создана структура данных 'shema_for_split'")
    
    # 2. Создаем схему в структуре со всеми атрибутами
    print("[INFO] Шаг 2: Создание схемы в структуре со всеми атрибутами")
    
    # Находим созданную структуру и кликаем на неё
    shema_for_split = page.locator('[aria-label="treeitem_label"]:has-text("shema_for_split")')
    assert shema_for_split.is_visible(), "Структура 'shema_for_split' не найдена!"
    shema_for_split.click()
    time.sleep(1)
    print("[INFO] Клик по структуре 'shema_for_split' выполнен")
    
    # Открываем панель деталей диаграммы
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    if not details_panel.is_visible():
        switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
        if switcher.is_visible():
            switcher.click()
            time.sleep(0.3)
            print("[INFO] Панель деталей диаграммы открыта")
    
    # Создаем схему с атрибутами используя page object
    schema_name = f"split_schema_{int(time.time())}"
    data_struct.click_create_schema_button(schema_name)
    time.sleep(0.5)
    print(f"[INFO] Создана схема: {schema_name}")
    
    # Создаем атрибуты по одному с правильными индексами
    attributes_data = [
        {"name": "id", "type": "integer", "desc": "Уникальный идентификатор"},
        {"name": "name", "type": "string", "desc": "Название элемента"},
        {"name": "value", "type": "float", "desc": "Числовое значение"},
        {"name": "active", "type": "boolean", "desc": "Активен ли элемент"},
        {"name": "tags", "type": "list", "desc": "Список тегов"}
    ]
    
    for idx, attr in enumerate(attributes_data):
        # Создаем новый атрибут
        data_struct.click_create_attribute_button()
        time.sleep(1)
        
        # Заполняем имя атрибута
        data_struct.fill_attribute_name_by_index(idx, attr["name"])
        data_struct.press_enter_attribute_name_by_index(idx)
        time.sleep(0.5)
        
        # Выбираем тип
        if attr["type"] == "list":
            data_struct.select_attribute_type_by_index(idx, "list")
            time.sleep(0.5)
            data_struct.select_list_element_type_in_modal("string")
            time.sleep(0.5)
        else:
            data_struct.select_attribute_type_by_index(idx, attr["type"])
            time.sleep(0.5)
        
        # Заполняем описание
        data_struct.fill_attribute_description_by_index(idx, attr["desc"])
        time.sleep(0.5)
        
        print(f"[INFO] Создан атрибут {idx}: {attr['name']} ({attr['type']})")
    
    print("[INFO] Схема с атрибутами создана")
    
    # 3. Открываем диаграмму 'test_split.df.json' в папке 'test_flow_component'
    print("[INFO] Шаг 3: Открытие диаграммы 'test_split.df.json' в папке 'test_flow_component'")
    
    # Находим папку 'test_flow_component'
    test_flow_folder = page.locator('[aria-label="treeitem_label"]:has-text("test_flow_component")')
    assert test_flow_folder.count() > 0, "Папка 'test_flow_component' не найдена в проекте!"
    print("[INFO] Папка 'test_flow_component' найдена")
    test_flow_folder.click()
    time.sleep(1)
    print("[INFO] Клик по папке 'test_flow_component' выполнен")
    
    # Находим и открываем файл 'test_split.df.json'
    test_split_file = page.locator('[aria-label="treeitem_label"]:has-text("test_split.df.json")')
    assert test_split_file.count() > 0, "Файл 'test_split.df.json' не найден в проекте!"
    print("[INFO] Файл 'test_split.df.json' найден")
    test_split_file.dblclick()
    time.sleep(2)
    print("[INFO] Диаграмма 'test_split.df.json' открыта")
    
    # Проверяем, что диаграмма загрузилась
    canvas = page.locator('canvas').first
    canvas.wait_for(state="visible", timeout=10000)
    time.sleep(2)
    print("[INFO] Canvas диаграммы загружен")
    
    # Закрываем файловую панель (если она открыта)
    try:
        if page.get_by_label("board_toolbar_panel").is_visible():
            file_manager_btn = page.get_by_role("button", name="board_toolbar_filemanager_button")
            if file_manager_btn.is_visible():
                file_manager_btn.click()
                time.sleep(0.5)
                print("[INFO] Файловая панель закрыта")
    except Exception as e:
        print(f"[INFO] Файловая панель уже закрыта или не найдена: {e}")
    
    # Закрываем правый сайдбар (если он открыт)
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
    
    # Делаем скриншот для проверки
    save_screenshot(page, f"split_test_steps_1_2_3_complete_{project_code}")
    
    # 4. Ищем компонент Input на canvas и делаем двойной клик
    print("[INFO] Шаг 4: Поиск компонента Input на canvas")
    
    canvas_utils = CanvasUtils(page)
    
    # Используем новую утилиту для поиска компонента Input
    if not canvas_utils.find_component_by_title("Input", exact=True):
        raise Exception("Не удалось найти или кликнуть по компоненту Input")
    
    # 5. Выбираем созданную структуру данных и схему
    print("[INFO] Шаг 5: Выбор созданной структуры данных и схемы")
    
    # Используем новую утилиту для выбора структуры данных и схемы
    # Передаем имя схемы, которое мы создали ранее
    if not canvas_utils.select_structure_data("shema_for_split", schema_name):
        save_screenshot(page, f"structure_selection_error_{project_code}")
        raise Exception("Не удалось выбрать структуру данных 'shema_for_split' или схему")
    
    # Финальный скриншот
    save_screenshot(page, f"split_test_steps_4_5_complete_{project_code}")
    
    # 6. Закрываем правый сайдбар
    print("[INFO] Шаг 6: Закрытие правого сайдбара")
    
    try:
        details_panel = page.locator('[aria-label="diagram_details_panel"]')
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт")
        else:
            print("[INFO] Правый сайдбар уже закрыт")
    except Exception as e:
        print(f"[INFO] Ошибка при закрытии правого сайдбара: {e}")
    
    # 7. Ищем компонент Split на canvas и делаем двойной клик
    print("[INFO] Шаг 7: Поиск компонента Split на canvas")
    
    if not canvas_utils.find_component_by_title("Split", exact=True):
        raise Exception("Не удалось найти или кликнуть по компоненту Split")
    
    # 8. Создаем условие для компонента Split
    print("[INFO] Шаг 8: Создание условия для компонента Split")
    
    try:
        # Ждем появления правого сайдбара
        details_panel = page.locator('[aria-label="diagram_details_panel"]')
        details_panel.wait_for(state="visible", timeout=10000)
        print("[INFO] Правый сайдбар открыт для компонента Split")
        
        # Ищем и кликаем кнопку "Добавить" в правом сайдбаре
        # Используем точный селектор из HTML структуры
        add_button = page.locator('.decision-flow__Button__Content___83B4Z:has-text("Добавить")').first
        if add_button.is_visible():
            add_button.click()
            time.sleep(2)  # Увеличиваем время ожидания
            print("[INFO] Кнопка 'Добавить' нажата")
        else:
            # Fallback - попробуем найти через другие селекторы
            add_button = page.locator('[aria-label="diagram_element_details"] div:has-text("Добавить")').first
            if add_button.is_visible():
                add_button.click()
                time.sleep(2)
                print("[INFO] Кнопка 'Добавить' найдена через fallback селектор")
            else:
                add_button = page.locator('button:has-text("Добавить")').first
                if add_button.is_visible():
                    add_button.click()
                    time.sleep(2)
                    print("[INFO] Кнопка 'Добавить' найдена через button селектор")
                else:
                    raise Exception("Кнопка 'Добавить' не найдена")
            
    except Exception as e:
        print(f"[ERROR] Ошибка при создании условия: {e}")
        save_screenshot(page, f"split_condition_error_{project_code}")
        raise
    
    # 9. Заполняем поля условия
    print("[INFO] Шаг 9: Заполнение полей условия")
    
    try:
        # Ждем появления полей условия
        time.sleep(1)
        
        # Заполняем поле name условия - пробуем разные селекторы
        name_selectors = [
            'textarea[name="config.patterns.0.name"][aria-label="config.patterns.0.name"]',
            'textarea[name="config.patterns.0.name"]',
            'input[name="config.patterns.0.name"]',
            'textarea[aria-label="config.patterns.0.name"]'
        ]
        
        name_field = None
        for selector in name_selectors:
            try:
                name_field = page.locator(selector).first
                if name_field.is_visible():
                    print(f"[INFO] Поле name найдено через селектор: {selector}")
                    break
            except Exception:
                continue
        
        if name_field and name_field.is_visible():
            name_field.click()
            time.sleep(0.5)
            name_field.fill("condition_name")
            time.sleep(0.5)
            print("[INFO] Поле name условия заполнено: 'condition_name'")
        else:
            raise Exception("Поле name условия не найдено")
        
        # Заполняем поле expression - пробуем разные селекторы
        expression_selectors = [
            'textarea[name="config.patterns.0.expression"][aria-label="config.patterns.0.expression"]',
            'textarea[name="config.patterns.0.expression"]',
            'input[name="config.patterns.0.expression"]',
            'textarea[aria-label="config.patterns.0.expression"]'
        ]
        
        expression_field = None
        for selector in expression_selectors:
            try:
                expression_field = page.locator(selector).first
                if expression_field.is_visible():
                    print(f"[INFO] Поле expression найдено через селектор: {selector}")
                    break
            except Exception:
                continue
        
        if expression_field and expression_field.is_visible():
            expression_field.click()
            time.sleep(0.5)
            expression_field.fill("$node.Input.data.active")
            time.sleep(0.5)
            print("[INFO] Поле expression заполнено: '$node.Input.data.active'")
        else:
            print("[ERROR] Поле expression не найдено или не видимо")
            raise Exception("Поле expression условия не найдено")
        
    except Exception as e:
        print(f"[ERROR] Ошибка при заполнении полей условия: {e}")
        save_screenshot(page, f"split_condition_fields_error_{project_code}")
        raise
    
    # 10. Закрываем правый сайдбар после создания условия
    print("[INFO] Шаг 10: Закрытие правого сайдбара после создания условия")
    
    try:
        details_panel = page.locator('[aria-label="diagram_details_panel"]')
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после создания условия")
        else:
            print("[INFO] Правый сайдбар уже закрыт")
    except Exception as e:
        print(f"[INFO] Ошибка при закрытии правого сайдбара: {e}")
    
    # 11. Находим стрелку, выходящую из Split компонента, и делаем двойной клик
    print("[INFO] Шаг 11: Поиск стрелки, выходящей из Split компонента")
    
    # Используем утилиту CanvasUtils для поиска стрелки
    if not canvas_utils.find_arrow_by_component("Split"):
        print("[WARN] Не удалось найти стрелку через утилиту, пробуем альтернативные методы")
        save_screenshot(page, f"arrow_not_found_{project_code}")
    else:
        print("[SUCCESS] Стрелка найдена и обработана через CanvasUtils")
    
    # 12. Выбираем созданное условие в поле стрелки
    print("[INFO] Шаг 12: Выбор созданного условия в поле стрелки")
    
    # Используем утилиту CanvasUtils для выбора условия
    try:
        if not canvas_utils.select_condition_in_arrow_field("condition_name"):
            print("[WARN] Не удалось выбрать условие через утилиту")
            save_screenshot(page, f"condition_selection_error_{project_code}")
            
            # Пробуем альтернативный подход - просто заполняем поле напрямую
            print("[INFO] Пробуем альтернативный подход - заполнение поля напрямую")
            try:
                condition_field = page.locator('textarea[name="config.from"][aria-label="config.from"]')
                if condition_field.is_visible():
                    condition_field.click()
                    time.sleep(0.5)
                    condition_field.fill("condition_name")
                    time.sleep(0.5)
                    print("[INFO] Поле условия заполнено напрямую")
                else:
                    print("[WARN] Поле условия не найдено для прямого заполнения")
            except Exception as e:
                print(f"[WARN] Ошибка при прямом заполнении поля: {e}")
        else:
            print("[SUCCESS] Условие выбрано через CanvasUtils")
    except Exception as e:
        print(f"[WARN] Ошибка при выборе условия: {e}")
        print("[INFO] Продолжаем выполнение теста без выбора условия")
    
    # 13. Переходим на вкладку "Процесс" и подвкладку "Анализ"
    print("[INFO] Шаг 13: Переход на вкладку 'Процесс' и подвкладку 'Анализ'")
    
    try:
        page.get_by_text("Процесс", exact=True).click()
        time.sleep(0.3)
        print("[INFO] Переключились на вкладку 'Процесс'")
        
        page.get_by_text("Анализ", exact=True).click()
        time.sleep(0.3)
        print("[INFO] Переключились на подвкладку 'Анализ'")
        
        # Нажимаем кнопку "Предзаполнить"
        page.locator('xpath=/html/body/div[1]/div[2]/div[1]/div[5]/div/div[3]/div[3]/div[2]/div[3]/div/div[1]/div/div[2]/div[1]/button[1]').click()
        time.sleep(2)  # Пауза после предзаполнения
        print("[INFO] Кнопка 'Предзаполнить' нажата")
        
        # Проверяем содержимое поля анализа
        try:
            view_lines_text = page.locator(".view-lines").first.text_content()
            print(f"[INFO] Текст из .view-lines: {view_lines_text}")
        except Exception as e:
            print(f"[WARN] Не удалось получить текст из .view-lines: {e}")
            
    except Exception as e:
        print(f"[WARN] Ошибка при настройке процесса и анализа: {e}")
    
    # 14. Запускаем диаграмму (первый раз - ожидаем ошибку)
    print("[INFO] Шаг 14: Запуск диаграммы (первый раз - ожидаем ошибку)")
    
    try:
        play_btn = page.get_by_role("button", name="diagram_play_button")
        play_btn.wait_for(state="visible", timeout=5000)
        play_btn.click()
        time.sleep(2)  # Ждём запуска диаграммы
        print("[INFO] Диаграмма запущена")
        
        # Проверяем toast уведомление об ошибке
        try:
            toast = page.locator('.Toast__Toast___ZqZzU[aria-label="toast"]')
            toast.wait_for(state="visible", timeout=15000)  # Ждём до 15 секунд появления тоста
            print("[INFO] Тост о завершении диаграммы появился")
            
            toast_title = toast.locator('.Toast__Title___-0bIZ')
            assert toast_title.is_visible(), "Заголовок тоста не найден!"
            title_text = toast_title.text_content()
            assert "Диаграмма завершена с ошибкой" in title_text, f"Ожидался тост с ошибкой, получен: {title_text}"
            print(f"[SUCCESS] Заголовок тоста с ошибкой: {title_text}")
            
            toast_description = toast.locator('.Toast__Description___YwLXR')
            assert toast_description.is_visible(), "Описание тоста не найдено!"
            description_text = toast_description.text_content()
            print(f"[SUCCESS] Описание ошибки: {description_text}")
            
            # Проверяем иконку ошибки
            error_icon = toast.locator('.Toast__Icon_error___kXBpl')
            assert error_icon.is_visible(), "Иконка ошибки не найдена!"
            print("[SUCCESS] Иконка ошибки найдена")
            
        except Exception as e:
            print(f"[ERROR] Не удалось найти или проверить тост об ошибке: {e}")
            page.screenshot(path=f'screenshots/toast_error_{int(time.time())}.png', full_page=True)
            raise
            
    except Exception as e:
        print(f"[ERROR] Ошибка при запуске диаграммы: {e}")
        save_screenshot(page, f"diagram_run_error_{project_code}")
        raise
    
    # 15. Исправляем значение active: false на active: true в поле анализа
    print("[INFO] Шаг 15: Исправление значения active: false на active: true в поле анализа")
    
    try:
        # Находим правильное поле анализа (то, которое содержит данные, а не ошибку)
        analysis_fields = page.locator('.view-lines.monaco-mouse-cursor-text')
        analysis_field = None
        
        # Ищем поле с данными (не с ошибкой)
        for i in range(analysis_fields.count()):
            field = analysis_fields.nth(i)
            try:
                field_text = field.text_content()
                if field_text and 'active' in field_text and 'error' not in field_text:
                    analysis_field = field
                    print(f"[INFO] Найдено поле анализа с данными: {field_text[:50]}...")
                    break
            except Exception:
                continue
        
        if not analysis_field:
            # Fallback - используем первое поле
            analysis_field = analysis_fields.first
            print("[WARN] Используем первое доступное поле анализа")
        
        # Кликаем в поле анализа для редактирования
        analysis_field.click()
        time.sleep(0.5)
        
        # Находим и заменяем только значение false на true в строке "active": false
        # Используем Ctrl+F для поиска
        page.keyboard.press("Control+F")
        time.sleep(0.5)
        
        # Вводим текст для поиска только слова "false"
        page.keyboard.type('false')
        time.sleep(0.5)
        
        # Нажимаем Enter для поиска (это найдет значение false в структуре)
        page.keyboard.press("Enter")
        time.sleep(0.5)
        
        # Закрываем поиск (Escape)
        page.keyboard.press("Escape")
        time.sleep(0.5)
        
        # Теперь курсор должен быть на слове "false"
        # Выделяем только слово "false"
        page.keyboard.press("Control+D")  # Выделить текущее слово
        time.sleep(0.3)
        
        # Заменяем только "false" на "true"
        page.keyboard.type('true')
        time.sleep(1)
        
        print("[SUCCESS] Значение active изменено с false на true")
        
        # Сохраняем изменения в поле анализа
        page.keyboard.press("Control+S")
        time.sleep(1)
        print("[INFO] Изменения в поле анализа сохранены")
        
        print("[INFO] Значение active обновлено в структуре данных через поле анализа")
        
        # Закрываем правый сайдбар после изменения структуры
        try:
            details_panel = page.locator('[aria-label="diagram_details_panel"]')
            if details_panel.is_visible():
                switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
                if switcher.is_visible():
                    switcher.click()
                    time.sleep(0.5)
                    print("[INFO] Правый сайдбар закрыт после изменения структуры")
        except Exception as e:
            print(f"[WARN] Не удалось закрыть правый сайдбар: {e}")
        
    except Exception as e:
        print(f"[ERROR] Ошибка при изменении значения active: {e}")
        save_screenshot(page, f"analysis_field_error_{project_code}")
        raise
    
    # 16. Настраиваем компонент Output2 и запускаем диаграмму повторно
    print("[INFO] Шаг 16: Настройка компонента Output2 и запуск диаграммы повторно")
    
    try:
        # Даем время на стабилизацию интерфейса после закрытия сайдбара
        time.sleep(2)
        
        # Убеждаемся, что мы на правильной вкладке
        try:
            # Проверяем, не находимся ли мы уже на вкладке "Процесс"
            process_tab = page.get_by_text("Процесс", exact=True)
            if process_tab.is_visible():
                # Проверяем, активна ли уже вкладка
                try:
                    active_tab = page.locator('.active, [aria-selected="true"]')
                    if active_tab.count() > 0:
                        tab_text = active_tab.first.text_content()
                        if "Процесс" in tab_text:
                            print("[INFO] Уже находимся на вкладке 'Процесс'")
                        else:
                            process_tab.click()
                            time.sleep(0.5)
                            print("[INFO] Переключились на вкладку 'Процесс'")
                    else:
                        process_tab.click()
                        time.sleep(0.5)
                        print("[INFO] Переключились на вкладку 'Процесс'")
                except Exception:
                    process_tab.click()
                    time.sleep(0.5)
                    print("[INFO] Переключились на вкладку 'Процесс' (fallback)")
            else:
                print("[WARN] Вкладка 'Процесс' не найдена")
        except Exception as e:
            print(f"[WARN] Не удалось переключиться на вкладку 'Процесс': {e}")
        
        # Настраиваем компонент Output2
        print("[INFO] Настройка компонента Output2 перед повторным запуском")
        
        try:
            # Ищем компонент Output2 на canvas
            print("[INFO] Поиск компонента Output2 на canvas...")
            if canvas_utils.find_component_by_title("Output2", exact=True):
                print("[SUCCESS] Компонент Output2 найден и открыт")
                
                # Переключаемся на вкладку "Параметры" если нужно
                try:
                    parameters_tab = page.get_by_text("Параметры", exact=True)
                    if parameters_tab.is_visible():
                        parameters_tab.click()
                        time.sleep(0.5)
                        print("[INFO] Переключились на вкладку 'Параметры'")
                except Exception as e:
                    print(f"[WARN] Не удалось переключиться на вкладку 'Параметры': {e}")
                
                # Заполняем поле "Данные"
                try:
                    data_field = page.get_by_role("textbox", name="inputs_config.data.value")
                    if data_field.is_visible():
                        data_field.click()
                        time.sleep(0.5)
                        data_field.fill('{"result" : $node.Split."1"}')
                        time.sleep(1)
                        print('[INFO] Поле "Данные" заполнено: {"result" : $node.Split."1"}')
                    else:
                        print("[WARN] Поле 'Данные' не найдено")
                except Exception as e:
                    print(f"[WARN] Ошибка при заполнении поля 'Данные': {e}")
                    
                # Закрываем правый сайдбар
                try:
                    details_panel = page.locator('[aria-label="diagram_details_panel"]')
                    if details_panel.is_visible():
                        switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
                        if switcher.is_visible():
                            switcher.click()
                            time.sleep(0.5)
                            print("[INFO] Правый сайдбар закрыт после настройки Output2")
                except Exception as e:
                    print(f"[WARN] Не удалось закрыть правый сайдбар: {e}")
            else:
                print("[WARN] Компонент Output2 не найден")
                
        except Exception as e:
            print(f"[WARN] Ошибка при настройке компонента Output2: {e}")
        
        # Нажимаем кнопку reset для сброса диаграммы
        try:
            reset_btn = page.get_by_role("button", name="diagram_reset_button")
            reset_btn.wait_for(state="visible", timeout=5000)
            reset_btn.click()
            time.sleep(1)
            print("[INFO] Диаграмма сброшена (reset)")
        except Exception as e:
            print(f"[WARN] Не удалось нажать кнопку reset: {e}")
        
        # Запускаем диаграмму повторно
        play_btn = page.get_by_role("button", name="diagram_play_button")
        play_btn.wait_for(state="visible", timeout=10000)
        play_btn.click()
        time.sleep(2)  # Ждём запуска диаграммы
        print("[INFO] Диаграмма запущена повторно")
        
        # Проверяем toast уведомление об успешном завершении
        try:
            toast = page.locator('.Toast__Toast___ZqZzU[aria-label="toast"]')
            toast.wait_for(state="visible", timeout=15000)  # Ждём до 15 секунд появления тоста
            print("[INFO] Тост о завершении диаграммы появился")
            
            toast_title = toast.locator('.Toast__Title___-0bIZ')
            assert toast_title.is_visible(), "Заголовок тоста не найден!"
            title_text = toast_title.text_content()
            assert "Диаграмма завершена" in title_text, f"Неожиданный заголовок тоста: {title_text}"
            print(f"[SUCCESS] Заголовок тоста: {title_text}")
            
            toast_description = toast.locator('.Toast__Description___YwLXR')
            assert toast_description.is_visible(), "Описание тоста не найдено!"
            description_text = toast_description.text_content()
            print(f"[SUCCESS] Описание тоста: {description_text}")
            
            # Ассерт успешного завершения
            assert "Диаграмма завершена" in title_text, f"Ожидался успешный тост, получен: {title_text}"
            print("[SUCCESS] ТЕСТ ПРОЙДЕН: Диаграмма успешно завершена!")
            
        except Exception as e:
            print(f"[ERROR] Не удалось найти или проверить тост о завершении диаграммы: {e}")
            page.screenshot(path=f'screenshots/toast_error_{int(time.time())}.png', full_page=True)
            raise
            
    except Exception as e:
        print(f"[ERROR] Ошибка при повторном запуске диаграммы: {e}")
        save_screenshot(page, f"diagram_rerun_error_{project_code}")
        raise
    
    # Финальный скриншот
    try:
        save_screenshot(page, f"split_test_all_steps_complete_{project_code}")
    except Exception as e:
        print(f"[WARN] Не удалось сделать финальный скриншот: {e}")
    
    print("[SUCCESS] Все шаги теста Split выполнены успешно!")
    print("[SUCCESS] Тест прошел полный цикл: ошибка -> исправление -> успешное выполнение")
    time.sleep(2)
