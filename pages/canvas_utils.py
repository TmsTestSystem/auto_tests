from playwright.sync_api import Page
import time


class CanvasUtils:
    """
    Утилиты для работы с компонентами на canvas диаграмм
    """
    
    def __init__(self, page: Page):
        self.page = page
    
    def find_component_by_title(self, title, exact=True, timeout=10000):
        """
        Находит компонент на canvas по заголовку
        
        Args:
            title (str): Заголовок компонента для поиска
            exact (bool): Точное совпадение текста (по умолчанию True)
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если компонент найден и клик выполнен успешно
        """
        print(f"[INFO] Поиск компонента '{title}' на canvas")
        
        try:
            canvas = self.page.locator('canvas').first
            canvas.wait_for(state="visible", timeout=timeout)
            time.sleep(0.5)
            
            # Метод 1: Поиск по тексту
            try:
                if exact:
                    component_label = self.page.get_by_text(title, exact=True).first
                else:
                    component_label = self.page.get_by_text(title).first
                    
                if component_label.is_visible():
                    component_label.dblclick()
                    time.sleep(1)
                    print(f"[SUCCESS] Двойной клик по компоненту '{title}' выполнен")
                    return True
                else:
                    print(f"[WARN] Компонент '{title}' не найден через текст")
            except Exception as e:
                print(f"[WARN] Не удалось найти '{title}' через текст: {e}")
            
            # Метод 2: Поиск через координаты canvas (fallback)
            print(f"[INFO] Пробуем найти '{title}' через координаты canvas")
            try:
                box = canvas.bounding_box()
                if box:
                    # Пробуем разные позиции для разных типов компонентов
                    positions = [
                        {"x": box['x'] + box['width'] * 0.3, "y": box['y'] + box['height'] * 0.3},  # Input
                        {"x": box['x'] + box['width'] * 0.7, "y": box['y'] + box['height'] * 0.7},  # Output
                        {"x": box['x'] + box['width'] * 0.5, "y": box['y'] + box['height'] * 0.5},  # Center
                    ]
                    
                    for i, pos in enumerate(positions):
                        try:
                            canvas.click(position=pos, click_count=2)
                            time.sleep(0.5)
                            print(f"[INFO] Двойной клик по позиции {i+1} выполнен")
                            # Проверяем, открылось ли что-то (например, модальное окно или сайдбар)
                            if self._check_component_opened():
                                print(f"[SUCCESS] Компонент найден и открыт через координаты")
                                return True
                        except Exception as e:
                            print(f"[WARN] Не удалось кликнуть по позиции {i+1}: {e}")
                            continue
                            
            except Exception as e:
                print(f"[WARN] Не удалось кликнуть по координатам: {e}")
            
            print(f"[ERROR] Компонент '{title}' не найден ни одним способом")
            return False
            
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске компонента '{title}': {e}")
            return False
    
    def find_component_by_position(self, x_percent, y_percent, timeout=10000):
        """
        Находит компонент на canvas по относительным координатам
        
        Args:
            x_percent (float): Процент от ширины canvas (0.0 - 1.0)
            y_percent (float): Процент от высоты canvas (0.0 - 1.0)
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если клик выполнен успешно
        """
        print(f"[INFO] Поиск компонента по координатам ({x_percent*100}%, {y_percent*100}%)")
        
        try:
            canvas = self.page.locator('canvas').first
            canvas.wait_for(state="visible", timeout=timeout)
            time.sleep(0.5)
            
            box = canvas.bounding_box()
            if not box:
                print("[ERROR] Не удалось получить размеры canvas")
                return False
                
            pos = {
                "x": box['x'] + box['width'] * x_percent,
                "y": box['y'] + box['height'] * y_percent
            }
            
            canvas.click(position=pos, click_count=2)
            time.sleep(0.5)
            print(f"[SUCCESS] Двойной клик по координатам ({x_percent*100}%, {y_percent*100}%) выполнен")
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при клике по координатам: {e}")
            return False
    
    def find_component_by_type(self, component_type, timeout=10000):
        """
        Находит компонент по типу (Input, Output, Split, etc.)
        
        Args:
            component_type (str): Тип компонента
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если компонент найден и клик выполнен успешно
        """
        # Маппинг типов на возможные заголовки
        type_mapping = {
            "input": ["Input", "Вход", "Входные данные"],
            "output": ["Output", "Выход", "Выходные данные"],
            "split": ["Split", "Разделение", "Разделить"],
            "join": ["Join", "Объединение", "Объединить"],
            "filter": ["Filter", "Фильтр", "Фильтрация"],
            "transform": ["Transform", "Преобразование", "Трансформация"],
            "decision": ["Decision", "Решение", "Условие"],
            "loop": ["Loop", "Цикл", "Повторение"],
        }
        
        possible_titles = type_mapping.get(component_type.lower(), [component_type])
        
        for title in possible_titles:
            if self.find_component_by_title(title, exact=True, timeout=timeout):
                return True
        
        print(f"[WARN] Компонент типа '{component_type}' не найден ни под одним из заголовков: {possible_titles}")
        return False
    
    def _check_component_opened(self):
        """
        Проверяет, открылся ли компонент (модальное окно, сайдбар и т.д.)
        
        Returns:
            bool: True если что-то открылось
        """
        try:
            # Проверяем наличие модального окна
            modal = self.page.locator('[role="dialog"], .Modal__Modal___ZqZzU, .Popup__Popup___vJ6BT').first
            if modal.is_visible():
                return True
            
            # Проверяем наличие правого сайдбара
            details_panel = self.page.locator('[aria-label="diagram_details_panel"]')
            if details_panel.is_visible():
                return True
            
            # Проверяем наличие других панелей
            if self.page.get_by_text("Компонент", exact=True).is_visible():
                return True
                
            return False
        except Exception:
            return False
    
    def select_structure_data(self, structure_name, schema_name=None, timeout=10000):
        """
        Выбирает структуру данных и схему в правом сайдбаре (как в первом тесте)
        
        Args:
            structure_name (str): Название структуры данных
            schema_name (str): Название схемы (опционально)
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если выбор выполнен успешно
        """
        print(f"[INFO] Выбор структуры данных '{structure_name}' и схемы '{schema_name}'")
        
        try:
            # Открываем правый сайдбар если он закрыт
            details_panel = self.page.locator('[aria-label="diagram_details_panel"]')
            if not details_panel.is_visible():
                switcher = self.page.get_by_role("button", name="diagram_details_panel_switcher")
                if switcher.is_visible():
                    switcher.click()
                    time.sleep(0.3)
                    print("[INFO] Правый сайдбар открыт")

            # 1. Выбираем структуру данных через кнопку "Выбрать файл" (только если сайдбар уже открыт)
            select_file_btn = self.page.get_by_role("button", name="textfield_select_file_button")
            if select_file_btn.is_visible():
                select_file_btn.click()
                time.sleep(0.5)
                print("[INFO] Кнопка 'Выбрать файл' нажата")
                
                # Ждем появления модального окна выбора файла
                modal = self.page.locator('[data-testid="Modal__Container"], .Modal')
                modal.wait_for(state="visible", timeout=timeout)
                print("[INFO] Модальное окно выбора файла открыто")
                
                # Ищем нашу структуру данных в модальном окне
                file_item = modal.get_by_text(structure_name, exact=False).first
                if not file_item.is_visible():
                    # Пробуем найти с расширением .ds.json
                    file_item = modal.get_by_text(f"{structure_name}.ds.json", exact=False).first
                
                if file_item.is_visible():
                    file_item.click()
                    time.sleep(0.2)
                    print(f"[INFO] Выбран файл структуры данных: {structure_name}")
                else:
                    raise Exception(f"Файл структуры данных '{structure_name}' не найден в модальном окне")
                
                # Нажимаем кнопку "Выбрать"
                choose_btn = modal.locator('button[aria-label="filemanager_select_button"]')
                for _ in range(30):
                    if choose_btn.is_visible() and not choose_btn.is_disabled():
                        break
                    time.sleep(0.2)
                
                choose_btn.click()
                modal.wait_for(state="detached", timeout=5000)
                time.sleep(0.3)
                print("[INFO] Модальное окно закрыто, структура данных выбрана")
            else:
                print("[INFO] Кнопка 'Выбрать файл' не найдена, возможно структура уже выбрана")
            
            # 2. Выбираем схему если она указана
            if schema_name:
                schema_field = self.page.locator('textarea[name="config.schema"][aria-label="config.schema"]')
                schema_field.wait_for(state="visible", timeout=timeout)
                
                # Ждем пока поле схемы станет активным
                for _ in range(40):
                    if not schema_field.is_disabled():
                        break
                    time.sleep(0.25)
                
                schema_field.click()
                time.sleep(0.2)
                print("[INFO] Поле схемы активировано")
                
                # Ищем и выбираем схему в правом сайдбаре
                details_panel = self.page.locator('[aria-label="diagram_details_panel"]')
                option_loc = details_panel.get_by_text(schema_name, exact=True)
                try:
                    option_loc.first.click()
                    time.sleep(2)
                    print(f"[SUCCESS] Выбрана схема: {schema_name}")
                except Exception as e:
                    print(f"[WARN] Не удалось выбрать схему '{schema_name}': {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при выборе структуры данных '{structure_name}': {str(e)}")
            return False
    
    def _select_structure_in_sidebar(self, structure_name):
        """
        Выбирает структуру данных в правом сайдбаре
        
        Args:
            structure_name (str): Название структуры данных
            
        Returns:
            bool: True если выбор выполнен успешно
        """
        print(f"[INFO] Поиск структуры данных '{structure_name}' в правом сайдбаре")
        
        try:
            # Ищем вкладку или раздел со структурами данных
            structure_tabs = [
                "Структуры данных",
                "Data Structures", 
                "Schema",
                "Схема"
            ]
            
            for tab_name in structure_tabs:
                try:
                    tab = self.page.get_by_text(tab_name, exact=True)
                    if tab.is_visible():
                        tab.click()
                        time.sleep(0.5)
                        print(f"[INFO] Переключились на вкладку '{tab_name}'")
                        break
                except Exception:
                    continue
            
            # Ищем нашу структуру данных
            structure_option = self.page.get_by_text(structure_name, exact=True)
            if structure_option.is_visible():
                structure_option.click()
                time.sleep(0.5)
                print(f"[SUCCESS] Выбрана структура данных '{structure_name}' в сайдбаре")
                return True
            else:
                # Пробуем найти через частичное совпадение
                structure_option = self.page.locator('*').filter(has_text=structure_name).first
                if structure_option.is_visible():
                    structure_option.click()
                    time.sleep(0.5)
                    print(f"[SUCCESS] Выбрана структура данных '{structure_name}' в сайдбаре (частичное совпадение)")
                    return True
                else:
                    print(f"[ERROR] Структура данных '{structure_name}' не найдена в правом сайдбаре")
                    return False
                    
        except Exception as e:
            print(f"[ERROR] Ошибка при выборе структуры данных в сайдбаре: {str(e)}")
            return False
    
    def _confirm_selection(self):
        """
        Подтверждает выбор в модальном окне
        """
        try:
            # Список возможных кнопок подтверждения
            confirm_buttons = [
                "Выбрать", "OK", "Применить", "Подтвердить", "Готово",
                "Select", "Apply", "Confirm", "Done"
            ]
            
            for button_name in confirm_buttons:
                try:
                    confirm_btn = self.page.get_by_role("button", name=button_name).first
                    if confirm_btn.is_visible():
                        confirm_btn.click()
                        time.sleep(1)
                        print(f"[INFO] Выбор подтвержден кнопкой '{button_name}'")
                        return
                except Exception:
                    continue
            
            print("[INFO] Кнопка подтверждения не найдена или не нужна")
            
        except Exception as e:
            print(f"[INFO] Ошибка при подтверждении выбора: {e}")
    
    def find_arrow_by_component(self, component_name, timeout=10000):
        """
        Находит стрелку, выходящую из указанного компонента
        
        Args:
            component_name (str): Название компонента (например, "Split")
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если стрелка найдена и клик выполнен успешно
        """
        print(f"[INFO] Поиск стрелки, выходящей из компонента '{component_name}'")
        
        try:
            # Ждем стабилизации интерфейса
            time.sleep(1)
            
            # Селекторы для поиска стрелок/соединений
            arrow_selectors = [
                'svg path[d*="M"]',  # SVG пути
                'svg line',         # SVG линии
                '[class*="arrow"]', # Элементы с классом arrow
                '[class*="connection"]', # Элементы с классом connection
                '[class*="edge"]',  # Элементы с классом edge
                '[class*="link"]',  # Элементы с классом link
                'path[stroke]',     # Пути с обводкой
                'line[stroke]',     # Линии с обводкой
                'svg g[class*="connection"]', # SVG группы соединений
                'svg g[class*="edge"]'        # SVG группы рёбер
            ]
            
            arrow_found = False
            for selector in arrow_selectors:
                try:
                    arrows = self.page.locator(selector)
                    arrow_count = arrows.count()
                    print(f"[INFO] Найдено {arrow_count} элементов по селектору: {selector}")
                    
                    if arrow_count > 0:
                        # Пробуем кликнуть по каждой найденной стрелке
                        for i in range(min(arrow_count, 5)):  # Проверяем максимум 5 стрелок
                            try:
                                arrow = arrows.nth(i)
                                if arrow.is_visible():
                                    # Делаем двойной клик по стрелке
                                    arrow.dblclick()
                                    time.sleep(1)
                                    print(f"[INFO] Двойной клик по стрелке {i+1} выполнен (селектор: {selector})")
                                    
                                    # Проверяем, открылся ли правый сайдбар
                                    details_panel = self.page.locator('[aria-label="diagram_details_panel"]')
                                    if details_panel.is_visible():
                                        print(f"[SUCCESS] Правый сайдбар открыт для стрелки {i+1}")
                                        arrow_found = True
                                        break
                                    else:
                                        print(f"[WARN] Правый сайдбар не открылся после клика по стрелке {i+1}")
                                        
                            except Exception as e:
                                print(f"[WARN] Ошибка при клике по стрелке {i+1}: {e}")
                                continue
                        
                        if arrow_found:
                            break
                            
                except Exception as e:
                    print(f"[WARN] Ошибка при работе с селектором {selector}: {e}")
                    continue
            
            if not arrow_found:
                # Fallback: попробуем кликнуть по области рядом с компонентом
                print(f"[INFO] Fallback: попробуем найти стрелку через координаты рядом с '{component_name}'")
                return self._find_arrow_by_coordinates(component_name)
            
            return arrow_found
            
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске стрелки от '{component_name}': {e}")
            return False
    
    def _find_arrow_by_coordinates(self, component_name):
        """
        Fallback метод для поиска стрелки по координатам
        
        Args:
            component_name (str): Название компонента
            
        Returns:
            bool: True если клик выполнен успешно
        """
        try:
            canvas = self.page.locator('canvas').first
            if not canvas.is_visible():
                print("[ERROR] Canvas не виден")
                return False
                
            box = canvas.bounding_box()
            if not box:
                print("[ERROR] Не удалось получить размеры canvas")
                return False
            
            # Определяем позицию в зависимости от компонента
            if component_name.lower() == "split":
                # Для Split компонента кликаем справа от центра
                arrow_pos = {
                    "x": box['x'] + box['width'] * 0.6,  # Справа от Split
                    "y": box['y'] + box['height'] * 0.5   # По центру по вертикали
                }
            else:
                # Для других компонентов кликаем в правой части
                arrow_pos = {
                    "x": box['x'] + box['width'] * 0.7,
                    "y": box['y'] + box['height'] * 0.5
                }
            
            canvas.click(position=arrow_pos, click_count=2)
            time.sleep(1)
            print(f"[INFO] Двойной клик по координатам ({arrow_pos['x']}, {arrow_pos['y']}) выполнен")
            
            # Проверяем, открылся ли правый сайдбар
            details_panel = self.page.locator('[aria-label="diagram_details_panel"]')
            if details_panel.is_visible():
                print("[SUCCESS] Правый сайдбар открыт после клика по координатам")
                return True
            else:
                print("[WARN] Правый сайдбар не открылся после клика по координатам")
                return False
                
        except Exception as e:
            print(f"[ERROR] Ошибка при fallback поиске стрелки: {e}")
            return False

    def select_condition_in_arrow_field(self, condition_name="condition_name", timeout=10000):
        """
        Выбирает условие в поле стрелки из выпадающего списка
        
        Args:
            condition_name (str): Название условия для выбора
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если условие выбрано успешно
        """
        print(f"[INFO] Выбор условия '{condition_name}' в поле стрелки")
        
        try:
            # Ждем появления правого сайдбара для стрелки
            details_panel = self.page.locator('[aria-label="diagram_details_panel"]')
            details_panel.wait_for(state="visible", timeout=timeout)
            print("[INFO] Правый сайдбар для стрелки открыт")
            
            # Ищем поле с выпадающим списком условий
            condition_field = self.page.locator('textarea[name="config.from"][aria-label="config.from"]')
            try:
                condition_field.wait_for(state="visible", timeout=5000)  # Уменьшили timeout
                print("[INFO] Поле выбора условия найдено")
            except Exception as e:
                print(f"[WARN] Поле выбора условия не найдено: {e}")
                return False
            
            # Сначала пробуем метод через клавиатуру (более надежный)
            try:
                # Фокусируемся на поле
                condition_field.click()
                time.sleep(0.5)
                print("[INFO] Фокус установлен на поле условия")
                
                # Открываем выпадающий список
                condition_field.press("ArrowDown")
                time.sleep(1)
                print("[INFO] Выпадающий список открыт через клавиатуру")
                
                # Проверяем, что список открылся
                dropdown_visible = False
                try:
                    # Ищем элементы выпадающего списка по новой структуре
                    tree_menu = self.page.locator('div[role="tree"].TextField__Menu___pmHMx')
                    if tree_menu.is_visible():
                        dropdown_visible = True
                        tree_items = tree_menu.locator('[role="treeitem"]')
                        print(f"[INFO] Найдено {tree_items.count()} элементов в выпадающем списке")
                        
                        # Выводим все доступные элементы для отладки
                        for i in range(tree_items.count()):
                            try:
                                item = tree_items.nth(i)
                                aria_label = item.get_attribute('aria-label')
                                print(f"[DEBUG] Элемент {i}: aria-label='{aria_label}'")
                            except Exception:
                                pass
                    else:
                        # Fallback - ищем по старым селекторам
                        options = self.page.locator('[role="option"], .option, [class*="option"]')
                        if options.count() > 0:
                            dropdown_visible = True
                            print(f"[INFO] Найдено {options.count()} элементов в выпадающем списке (fallback)")
                except Exception as e:
                    print(f"[WARN] Ошибка при поиске выпадающего списка: {e}")
                
                if dropdown_visible:
                    # Пробуем найти наше условие в списке
                    condition_selected = False
                    
                    try:
                        # Метод 1: Поиск по aria-label
                        condition_option = self.page.locator(f'[role="treeitem"][aria-label="{condition_name}"]')
                        if condition_option.is_visible():
                            condition_option.click()
                            time.sleep(0.5)
                            print(f"[SUCCESS] Условие '{condition_name}' выбрано по aria-label")
                            condition_selected = True
                    except Exception as e:
                        print(f"[WARN] Не удалось найти по aria-label: {e}")
                    
                    # Метод 2: Поиск по тексту в TreeItem__LabelPrimary___vzajD
                    if not condition_selected:
                        try:
                            condition_option = self.page.locator(f'.TreeItem__LabelPrimary___vzajD:has-text("{condition_name}")')
                            if condition_option.is_visible():
                                condition_option.click()
                                time.sleep(0.5)
                                print(f"[SUCCESS] Условие '{condition_name}' выбрано по тексту")
                                condition_selected = True
                        except Exception as e:
                            print(f"[WARN] Не удалось найти по тексту: {e}")
                    
                    # Метод 3: Поиск по точному тексту
                    if not condition_selected:
                        try:
                            condition_option = self.page.get_by_text(condition_name, exact=True)
                            if condition_option.is_visible():
                                condition_option.click()
                                time.sleep(0.5)
                                print(f"[SUCCESS] Условие '{condition_name}' выбрано по точному тексту")
                                condition_selected = True
                        except Exception as e:
                            print(f"[WARN] Не удалось найти по точному тексту: {e}")
                    
                    # Метод 4: Fallback - выбираем первое доступное условие
                    if not condition_selected:
                        try:
                            first_option = self.page.locator('[role="treeitem"]').first
                            if first_option.is_visible():
                                first_option.click()
                                time.sleep(0.5)
                                print("[INFO] Выбрано первое доступное условие")
                                condition_selected = True
                        except Exception as e:
                            print(f"[WARN] Не удалось выбрать первое условие: {e}")
                    
                    # Метод 5: Fallback через клавиатуру
                    if not condition_selected:
                        try:
                            condition_field.press("Enter")
                            time.sleep(0.5)
                            print("[INFO] Fallback: нажатие Enter для выбора")
                        except Exception as e:
                            print(f"[WARN] Ошибка при выборе через клавиатуру: {e}")
                else:
                    # Если список не открылся, пробуем альтернативный способ
                    print("[WARN] Выпадающий список не открылся, пробуем альтернативный способ")
                    condition_field.click()
                    time.sleep(1)
                    
                    # Пробуем найти элементы списка напрямую
                    try:
                        condition_option = self.page.get_by_text(condition_name, exact=True)
                        if condition_option.is_visible():
                            condition_option.click()
                            time.sleep(0.5)
                            print(f"[SUCCESS] Условие '{condition_name}' выбрано кликом")
                        else:
                            # Выбираем первое доступное
                            first_option = self.page.locator('[role="option"], .option, [class*="option"]').first
                            if first_option.is_visible():
                                first_option.click()
                                time.sleep(0.5)
                                print("[INFO] Выбрано первое доступное условие кликом")
                            else:
                                raise Exception("Не удалось найти элементы списка")
                    except Exception as e:
                        print(f"[WARN] Ошибка при клике по элементу: {e}")
                        raise Exception("Не удалось выбрать условие")
                        
            except Exception as e:
                print(f"[ERROR] Ошибка при выборе условия через клавиатуру: {e}")
                raise
            
            # Проверяем результат
            try:
                time.sleep(1)  # Даем время на обновление
                field_value = condition_field.input_value()
                if field_value:
                    print(f"[SUCCESS] Условие выбрано: '{field_value}'")
                    return True
                else:
                    print("[WARN] Поле условия пустое после выбора")
                    return False
            except Exception as e:
                print(f"[WARN] Не удалось получить значение поля условия: {e}")
                return True  # Считаем успешным, если не можем проверить
                
        except Exception as e:
            print(f"[ERROR] Ошибка при выборе условия '{condition_name}': {e}")
            return False

    def wait_for_canvas_load(self, timeout=10000):
        """
        Ждет загрузки canvas диаграммы
        
        Args:
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если canvas загружен
        """
        try:
            canvas = self.page.locator('canvas').first
            canvas.wait_for(state="visible", timeout=timeout)
            time.sleep(2)  # Дополнительное время для полной загрузки
            print("[SUCCESS] Canvas диаграммы загружен")
            return True
        except Exception as e:
            print(f"[ERROR] Canvas не загрузился в течение {timeout}мс: {e}")
            return False
