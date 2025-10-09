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
        
        if direction == "right":
            x = component_box['x'] + component_box['width']
            y = center_y
        elif direction == "left":
            x = component_box['x']
            y = center_y
        elif direction == "top":
            x = center_x
            y = component_box['y']
        elif direction == "bottom":
            x = center_x
            y = component_box['y'] + component_box['height']
        else:
            x = center_x
            y = center_y
        
        print(f"[INFO] Вычислены координаты точки соединения '{direction}': ({x}, {y})")
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
            
            # Определяем координаты целевой точки
            if to_direction == "center":
                to_x = to_component_box['x'] + to_component_box['width'] / 2
                to_y = to_component_box['y'] + to_component_box['height'] / 2
            else:
                to_point = self._calculate_connection_coordinates(to_component_box, to_direction)
                to_x = to_point['x']
                to_y = to_point['y']
            
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
    
    def create_connection_by_coordinates(self, from_x, from_y, to_x, to_y):
        """
        Создает соединение между двумя точками по координатам
        
        Args:
            from_x (float): X координата начальной точки
            from_y (float): Y координата начальной точки
            to_x (float): X координата конечной точки
            to_y (float): Y координата конечной точки
            
        Returns:
            bool: True если соединение создано успешно
        """
        print(f"[INFO] Создание соединения по координатам от ({from_x}, {from_y}) к ({to_x}, {to_y})")
        
        try:
            # Начинаем перетаскивание
            self.page.mouse.move(from_x, from_y)
            time.sleep(0.2)
            self.page.mouse.down(button="left")
            time.sleep(0.5)
            
            # Перетаскиваем до целевой точки
            self.page.mouse.move(to_x, to_y)
            time.sleep(0.5)
            
            # Отпускаем кнопку мыши
            self.page.mouse.up(button="left")
            time.sleep(1)
            
            print("[SUCCESS] Соединение создано по координатам")
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при создании соединения по координатам: {e}")
            return False
    
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
