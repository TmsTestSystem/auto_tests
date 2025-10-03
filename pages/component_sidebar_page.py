from playwright.sync_api import Page
from .base_page import BasePage
import time


class ComponentSidebarPage(BasePage):
    """Класс для работы с сайдбарами компонентов диаграммы"""
    
    def __init__(self, page: Page):
        super().__init__(page)
    
    def get_locator_center_position(self, locator):
        """Получить центральные координаты элемента"""
        box = locator.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            return {'x': x, 'y': y}
        return {'x': 0, 'y': 0}

    def get_component_center_position_by_title(self, component_title_locator):
        """Получить центральные координаты компонента по его заголовку.
        Центр компонента находится на 42px выше центра заголовка.
        """
        center = self.get_locator_center_position(component_title_locator)
        return {'x': center['x'], 'y': center['y'] - 42}

    def find_component_by_title(self, title_text):
        """Найти компонент по тексту заголовка"""
        # Ждём появления компонентов на диаграмме
        try:
            self.page.wait_for_selector('[aria-label="diagramComponentTitle"]', timeout=10000)
            time.sleep(1)  # Дополнительное время для стабилизации
        except Exception:
            print(f"[WARN] Компоненты диаграммы могут быть не загружены")
        
        return self.page.get_by_label('diagramComponentTitle').filter(has_text=title_text)

    def click_component_by_title(self, title_text, click_count=2, retries=3):
        """Кликнуть по компоненту по заголовку с ретраями
        
        Args:
            title_text: Текст заголовка компонента
            click_count: Количество кликов (1 - одинарный, 2 - двойной)
            retries: Количество попыток
            
        Returns:
            bool: True если клик успешен, False иначе
        """
        title_locator = self.find_component_by_title(title_text)
        if title_locator.count() == 0:
            # Отладка: выводим все найденные компоненты
            all_components = self.page.get_by_label('diagramComponentTitle')
            component_count = all_components.count()
            print(f"[DEBUG] Всего компонентов на диаграмме: {component_count}")
            if component_count > 0:
                for i in range(min(component_count, 5)):  # Выводим до 5 компонентов
                    try:
                        comp_text = all_components.nth(i).inner_text()
                        print(f"[DEBUG] Компонент {i+1}: '{comp_text}'")
                    except Exception:
                        print(f"[DEBUG] Компонент {i+1}: [не удалось получить текст]")
            print(f"[WARN] Компонент '{title_text}' не найден среди {component_count} компонентов")
            return False
        
        center_coords = self.get_component_center_position_by_title(title_locator.first)
        print(f"[INFO] Координаты центра компонента '{title_text}': {center_coords}")
        
        # Клик с ретраями
        for attempt in range(retries):
            try:
                self.page.mouse.click(center_coords['x'], center_coords['y'], click_count=click_count)
                time.sleep(0.4)
                
                # Проверяем, что панель деталей открылась (для двойного клика)
                if click_count == 2:
                    if self.page.locator('[aria-label="diagram_details_panel"]').is_visible():
                        return True
                else:
                    return True
                    
            except Exception as e:
                print(f"[WARN] Попытка клика {attempt+1} не удалась: {e}")
            
            # Небольшой сдвиг на повтор
            center_coords['x'] += 2
            center_coords['y'] += 2
        
        return False

    def open_sidebar_by_empty_click(self, component_center_coords, offset_x=70):
        """Открыть сайдбар кликом в пустое место рядом с компонентом
        
        Args:
            component_center_coords: Координаты центра компонента
            offset_x: Смещение по X от компонента
            
        Returns:
            bool: True если сайдбар открылся
        """
        try:
            empty_spot_x = component_center_coords['x'] + offset_x
            empty_spot_y = component_center_coords['y']
            self.page.mouse.click(empty_spot_x, empty_spot_y, click_count=2)
            time.sleep(1)
            print(f"[INFO] Двойной клик в пустое место ({empty_spot_x}, {empty_spot_y})")
            return True
        except Exception as e:
            print(f"[WARN] Не удалось выполнить клик в пустое место: {e}")
            return False

    def switch_to_analysis_tab(self):
        """Переключиться на вкладку 'Анализ' в сайдбаре"""
        try:
            analysis_tab = self.page.locator('input[aria-label="diagram_details_tab_analysis"][value="analysis"]')
            if analysis_tab.count() > 0:
                # Кликаем по родительскому label
                analysis_label = analysis_tab.locator('..').first
                analysis_label.click()
                time.sleep(0.5)
                print("[INFO] Переход на вкладку 'Анализ' выполнен")
                return True
            else:
                # Фолбэк: поиск по тексту "Анализ"
                self.page.get_by_text("Анализ").click()
                time.sleep(0.5)
                print("[INFO] Переход на вкладку 'Анализ' выполнен (фолбэк)")
                return True
        except Exception as e:
            print(f"[WARN] Не удалось перейти на вкладку 'Анализ': {e}")
            return False

    def get_sidebar_content(self):
        """Получить все содержимое сайдбара как текст"""
        try:
            sidebar_content = self.page.locator('[aria-label="diagram_details_panel"]')
            if sidebar_content.count() > 0:
                return sidebar_content.first.inner_text()
            else:
                print("[WARN] Сайдбар не найден")
                return ""
        except Exception as e:
            print(f"[WARN] Ошибка при получении содержимого сайдбара: {e}")
            return ""

    def find_field_in_sidebar(self, field_name, return_content=True):
        """Найти поле в сайдбаре по имени
        
        Args:
            field_name: Название поля (например, "Ответ", "Запрос")
            return_content: Возвращать содержимое поля или только факт наличия
            
        Returns:
            str|bool: Содержимое поля или True/False если return_content=False
        """
        try:
            # Поиск поля по различным селекторам
            possible_selectors = [
                f'div:has-text("{field_name}")',
                f'label:has-text("{field_name}")',
                f'[aria-label*="{field_name}"]',
                f'[data-field="{field_name.lower()}"]'
            ]
            
            field_element = None
            for selector in possible_selectors:
                elements = self.page.locator(selector)
                if elements.count() > 0:
                    field_element = elements.first
                    print(f"[INFO] Поле '{field_name}' найдено по селектору: {selector}")
                    break
            
            if field_element and return_content:
                try:
                    text = field_element.inner_text()
                    return text
                except Exception:
                    return field_element.text_content()
            elif field_element:
                return True
            else:
                # Поиск в общем содержимом сайдбара
                content = self.get_sidebar_content()
                if field_name in content:
                    if return_content:
                        # Извлекаем секцию после названия поля
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if field_name in line:
                                # Возвращаем несколько строк после найденного поля
                                field_lines = lines[i:i+10]
                                return '\n'.join(field_lines)
                    else:
                        return True
                
                return "" if return_content else False
                
        except Exception as e:
            print(f"[WARN] Ошибка при поиске поля '{field_name}': {e}")
            return "" if return_content else False

    def parse_response_field(self):
        """Специальный метод для парсинга поля 'Ответ' и извлечения JSON"""
        response_content = self.find_field_in_sidebar("Ответ")
        if response_content:
            print(f"[INFO] Содержимое поля 'Ответ':\n{response_content}")
            
            # Проверяем наличие ключевых данных
            if '"data": {}' in response_content:
                print("[SUCCESS] В ответе найдены данные: 'data': {}")
                return {"data": {}, "found": True}
            elif '{}' in response_content:
                print("[SUCCESS] В ответе найден символ {}")
                return {"data": "{}", "found": True}
            else:
                print("[WARN] В ответе не найдены ожидаемые данные")
                return {"data": None, "found": False}
        else:
            print("[WARN] Поле 'Ответ' не найдено")
            return {"data": None, "found": False}

    def fill_component_input_field(self, field_name, value):
        """Заполнить поле ввода в компоненте
        
        Args:
            field_name: Название поля (например, "inputs_config.data.value")
            value: Значение для ввода
            
        Returns:
            bool: True если заполнение успешно
        """
        try:
            field_selector = f'textarea[name="{field_name}"][aria-label="{field_name}"]'
            field = self.page.locator(field_selector)
            field.wait_for(state="visible", timeout=10000)
            field.fill(value)
            
            # Подтверждаем ввод
            try:
                field.press("Enter")
            except Exception:
                pass
            try:
                self.page.evaluate('(el) => el.blur()', field.element_handle())
            except Exception:
                pass
            
            print(f"[INFO] Поле '{field_name}' заполнено значением '{value}'")
            return True
            
        except Exception as e:
            print(f"[WARN] Не удалось заполнить поле '{field_name}': {e}")
            return False
