from playwright.sync_api import Page
import time


class ConnectionPage:
    """
    Страница для работы с соединениями между компонентами на диаграмме
    """
    
    def __init__(self, page: Page):
        self.page = page
    
    def find_connection_point(self, component_name, direction="right", timeout=5000):
        """
        Находит точку соединения для указанного компонента
        
        Args:
            component_name (str): Название компонента (например, "Input", "Output")
            direction (str): Направление точки соединения ("right", "left", "top", "bottom")
            timeout (int): Таймаут ожидания в миллисекундах
            
        Returns:
            dict: Словарь с координатами точки соединения или None если не найдена
        """
        print(f"[INFO] Поиск точки соединения '{direction}' для компонента '{component_name}'")
        
        try:
            # Сначала кликаем по компоненту, чтобы появились точки соединения
            component = self.page.get_by_text(component_name).first
            if not component.is_visible():
                print(f"[ERROR] Компонент '{component_name}' не найден")
                return None
                
            component.click()
            time.sleep(1)
            print(f"[INFO] Кликнули по компоненту '{component_name}', точки соединения должны появиться")
            
            # Получаем размеры компонента
            component_box = component.bounding_box()
            if not component_box:
                print(f"[ERROR] Не удалось получить размеры компонента '{component_name}'")
                return None
            
            # Центр компонента
            component_center_x = component_box['x'] + component_box['width'] / 2
            component_center_y = component_box['y'] + component_box['height'] / 2
            
            # Ищем элемент соединения по направлению
            connection_element = self._find_connection_element(component_name, direction, component_center_x, component_center_y)
            
            if connection_element:
                return connection_element
            else:
                # Fallback - вычисляем координаты точки соединения
                return self._calculate_connection_coordinates(component_box, direction)
                
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске точки соединения для '{component_name}': {e}")
            return None
    
    def _find_connection_element(self, component_name, direction, center_x, center_y):
        """
        Ищет элемент соединения на странице
        
        Args:
            component_name (str): Название компонента
            direction (str): Направление соединения
            center_x (float): X координата центра компонента
            center_y (float): Y координата центра компонента
            
        Returns:
            dict: Координаты элемента соединения или None
        """
        try:
            # Ищем все элементы соединения по направлению
            direction_elements = self.page.get_by_text(direction)
            connection_found = False
            
            for i in range(direction_elements.count()):
                try:
                    conn_element = direction_elements.nth(i)
                    if conn_element.is_visible():
                        # Получаем координаты элемента соединения
                        conn_box = conn_element.bounding_box()
                        if conn_box:
                            conn_x = conn_box['x'] + conn_box['width'] / 2
                            conn_y = conn_box['y'] + conn_box['height'] / 2
                            
                            # Проверяем расстояние от центра компонента
                            distance_x = abs(conn_x - center_x)
                            distance_y = abs(conn_y - center_y)
                            
                            # Если элемент находится рядом с компонентом (в пределах 100px)
                            if distance_x < 100 and distance_y < 100:
                                print(f"[SUCCESS] Найден элемент соединения '{direction}' для '{component_name}' на позиции ({conn_x}, {conn_y})")
                                return {
                                    'x': conn_x,
                                    'y': conn_y,
                                    'element': conn_element
                                }
                                
                except Exception as e:
                    print(f"[DEBUG] Ошибка при проверке элемента соединения {i}: {e}")
                    continue
            
            print(f"[WARN] Элемент соединения '{direction}' для '{component_name}' не найден")
            return None
            
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске элемента соединения: {e}")
            return None
    
    def _calculate_connection_coordinates(self, component_box, direction):
        """
        Вычисляет координаты точки соединения на основе размеров компонента
        
        Args:
            component_box (dict): Словарь с размерами компонента
            direction (str): Направление соединения
            
        Returns:
            dict: Координаты точки соединения
        """
        center_x = component_box['x'] + component_box['width'] / 2
        center_y = component_box['y'] + component_box['height'] / 2
        
        # Отступ от центра компонента на 33px в нужном направлении
        offset = 33
        
        if direction == "right":
            x = center_x + offset
            y = center_y
        elif direction == "left":
            x = center_x - offset
            y = center_y
        elif direction == "top":
            x = center_x
            y = center_y - offset
        elif direction == "bottom":
            x = center_x
            y = center_y + offset
        else:
            x = center_x
            y = center_y
        
        print(f"[INFO] Вычислены координаты точки соединения '{direction}' от центра ({center_x}, {center_y}) + {offset}px: ({x}, {y})")
        return {'x': x, 'y': y}
    
    def create_connection(self, from_component, to_component, from_direction="right", to_direction="left"):
        """
        Создает соединение между двумя компонентами
        
        Args:
            from_component (str): Название исходного компонента
            to_component (str): Название целевого компонента
            from_direction (str): Направление точки соединения у исходного компонента
            to_direction (str): Направление точки соединения у целевого компонента
            
        Returns:
            bool: True если соединение создано успешно
        """
        print(f"[INFO] Создание соединения от '{from_component}' ({from_direction}) к '{to_component}' ({to_direction})")
        
        try:
            # Находим точку соединения у исходного компонента
            from_point = self.find_connection_point(from_component, from_direction)
            if not from_point:
                print(f"[ERROR] Не удалось найти точку соединения для '{from_component}'")
                return False
            
            # Находим целевой компонент
            to_component_element = self.page.get_by_text(to_component).first
            if not to_component_element.is_visible():
                print(f"[ERROR] Целевой компонент '{to_component}' не найден")
                return False
            
            to_component_box = to_component_element.bounding_box()
            if not to_component_box:
                print(f"[ERROR] Не удалось получить размеры целевого компонента '{to_component}'")
                return False
            
            # Определяем координаты целевой точки - К ЦЕНТРУ компонента
            to_x = to_component_box['x'] + to_component_box['width'] / 2
            to_y = to_component_box['y'] + to_component_box['height'] / 2
            
            # Начинаем перетаскивание
            if 'element' in from_point:
                # Если нашли элемент соединения, кликаем по нему
                from_point['element'].click()
                time.sleep(0.2)
                self.page.mouse.down(button="left")
                time.sleep(0.5)
            else:
                # Иначе перемещаемся к координатам и начинаем перетаскивание
                self.page.mouse.move(from_point['x'], from_point['y'])
                time.sleep(0.2)
                self.page.mouse.down(button="left")
                time.sleep(0.5)
            
            # Перетаскиваем до целевой точки
            self.page.mouse.move(to_x, to_y)
            time.sleep(0.5)
            
            # Отпускаем кнопку мыши
            self.page.mouse.up(button="left")
            time.sleep(1)
            
            print(f"[SUCCESS] Соединение создано от '{from_component}' к '{to_component}'")
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при создании соединения: {e}")
            return False
    
    def create_connection_by_coordinates(self, from_x, from_y, to_x, to_y, from_direction="bottom"):
        """
        Создает соединение между двумя точками по координатам
        Ищет точку соединения внутри компонента (top, bottom, left, right)
        
        Args:
            from_x (float): X координата начальной точки
            from_y (float): Y координата начальной точки
            to_x (float): X координата конечной точки
            to_y (float): Y координата конечной точки
            from_direction (str): Направление точки соединения (top, bottom, left, right)
            
        Returns:
            bool: True если соединение создано успешно
        """
        print(f"[INFO] Создание соединения по координатам от ({from_x}, {from_y}) к ({to_x}, {to_y})")
        
        try:
            # Ищем точку соединения внутри компонента
            print(f"[INFO] Ищем точку соединения '{from_direction}' внутри компонента")
            connection_point = self._find_connection_point_inside_component(from_x, from_y, from_direction)
            
            if connection_point:
                print(f"[INFO] Найдена точка соединения '{from_direction}' в ({connection_point['x']}, {connection_point['y']})")
                start_x, start_y = connection_point['x'], connection_point['y']
            else:
                print(f"[WARN] Точка соединения '{from_direction}' не найдена, используем координаты компонента")
                start_x, start_y = from_x, from_y
            
            # Долгий тап на точке соединения
            print(f"[INFO] Выполняем долгий тап на точке соединения '{from_direction}'")
            self.page.mouse.move(start_x, start_y)
            time.sleep(0.2)
            
            # Долгий тап - держим кнопку мыши нажатой дольше
            self.page.mouse.down(button="left")
            time.sleep(1.5)  # Долгий тап
            
            # Перетаскиваем до целевой точки
            print(f"[INFO] Перетаскиваем от ({start_x}, {start_y}) к ({to_x}, {to_y})")
            self.page.mouse.move(to_x, to_y)
            time.sleep(0.5)
            
            # Отпускаем кнопку мыши
            self.page.mouse.up(button="left")
            time.sleep(1)
            
            print("[SUCCESS] Соединение создано по координатам (долгий тап)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при создании соединения по координатам: {e}")
            return False
    
    def _find_connection_point_near_coordinates(self, x, y, radius=50):
        """
        Ищет точку соединения в радиусе от указанных координат
        
        Args:
            x (float): X координата центра поиска
            y (float): Y координата центра поиска
            radius (int): Радиус поиска в пикселях
            
        Returns:
            dict: Координаты найденной точки соединения или None
        """
        try:
            # Ищем элементы, которые могут быть точками соединения
            connection_selectors = [
                'circle[cx][cy]',  # SVG круги
                'circle[fill]',    # Заполненные круги
                'circle[stroke]',  # Круги с обводкой
                '[class*="connection"]',  # Элементы с классом connection
                '[class*="anchor"]',      # Элементы с классом anchor
                '[class*="handle"]',      # Элементы с классом handle
                'div[style*="position: absolute"]',  # Абсолютно позиционированные div
                'svg > g > circle',      # Круги в SVG группах
                'svg > circle',          # Прямые круги в SVG
            ]
            
            for selector in connection_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            box = element.bounding_box()
                            if box:
                                # Проверяем, находится ли элемент в радиусе
                                elem_x = box['x'] + box['width'] / 2
                                elem_y = box['y'] + box['height'] / 2
                                
                                distance = ((elem_x - x) ** 2 + (elem_y - y) ** 2) ** 0.5
                                if distance <= radius:
                                    print(f"[DEBUG] Найдена потенциальная точка соединения: {selector} в ({elem_x}, {elem_y})")
                                    return {'x': elem_x, 'y': elem_y}
                except Exception as e:
                    continue
            
            print("[DEBUG] Точки соединения не найдены")
            return None
            
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске точки соединения: {e}")
            return None
    
    def _find_connection_point_inside_component(self, x, y, direction, radius=100):
        """
        Ищет точку соединения внутри компонента по направлению
        
        Args:
            x (float): X координата центра компонента
            y (float): Y координата центра компонента
            direction (str): Направление точки соединения (top, bottom, left, right)
            radius (int): Радиус поиска в пикселях
            
        Returns:
            dict: Координаты найденной точки соединения или None
        """
        try:
            print(f"[DEBUG] Ищем точку соединения '{direction}' внутри компонента в радиусе {radius}px от ({x}, {y})")
            
            # Ищем текст с направлением внутри компонента
            direction_element = self.page.get_by_text(direction, exact=True)
            
            if direction_element.is_visible():
                # Получаем координаты элемента направления
                box = direction_element.bounding_box()
                if box:
                    elem_x = box['x'] + box['width'] / 2
                    elem_y = box['y'] + box['height'] / 2
                    
                    # Проверяем, находится ли элемент в радиусе от компонента
                    distance = ((elem_x - x) ** 2 + (elem_y - y) ** 2) ** 0.5
                    if distance <= radius:
                        print(f"[DEBUG] Найдена точка соединения '{direction}' в ({elem_x}, {elem_y})")
                        return {'x': elem_x, 'y': elem_y}
                    else:
                        print(f"[DEBUG] Точка '{direction}' найдена, но слишком далеко: расстояние {distance:.1f}px")
                else:
                    print(f"[DEBUG] Не удалось получить координаты элемента '{direction}'")
            else:
                print(f"[DEBUG] Точка соединения '{direction}' не найдена")
            
            # Fallback: ищем по другим селекторам
            print(f"[DEBUG] Fallback: ищем точки соединения по альтернативным селекторам")
            alternative_selectors = [
                f'text="{direction}"',
                f'[aria-label*="{direction}"]',
                f'[title*="{direction}"]',
                f'[class*="{direction}"]',
            ]
            
            for selector in alternative_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            box = element.bounding_box()
                            if box:
                                elem_x = box['x'] + box['width'] / 2
                                elem_y = box['y'] + box['height'] / 2
                                
                                distance = ((elem_x - x) ** 2 + (elem_y - y) ** 2) ** 0.5
                                if distance <= radius:
                                    print(f"[DEBUG] Найдена альтернативная точка '{direction}' через селектор '{selector}' в ({elem_x}, {elem_y})")
                                    return {'x': elem_x, 'y': elem_y}
                except Exception:
                    continue
            
            print(f"[DEBUG] Точка соединения '{direction}' не найдена внутри компонента")
            return None
            
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске точки соединения внутри компонента: {e}")
            return None
    
    def find_and_click_connection_point(self, component_name, direction="right", timeout=5000):
        """
        Находит и кликает по точке соединения компонента
        
        Args:
            component_name (str): Название компонента
            direction (str): Направление точки соединения
            timeout (int): Таймаут ожидания
            
        Returns:
            bool: True если клик выполнен успешно
        """
        print(f"[INFO] Поиск и клик по точке соединения '{direction}' для '{component_name}'")
        
        try:
            connection_point = self.find_connection_point(component_name, direction, timeout)
            if not connection_point:
                return False
            
            if 'element' in connection_point:
                # Кликаем по элементу соединения
                connection_point['element'].click()
                time.sleep(0.2)
                return True
            else:
                # Кликаем по координатам
                self.page.mouse.move(connection_point['x'], connection_point['y'])
                time.sleep(0.2)
                self.page.mouse.click(connection_point['x'], connection_point['y'])
                time.sleep(0.2)
                return True
                
        except Exception as e:
            print(f"[ERROR] Ошибка при клике по точке соединения: {e}")
            return False
