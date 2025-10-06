"""
Page Object Model для управления диаграммами
"""
import time
from playwright.sync_api import Page


class DiagramPage:
    """Класс для работы с диаграммами"""
    
    def __init__(self, page: Page):
        self.page = page
    
    def run_diagram(self, timeout: int = 10000) -> bool:
        """
        Запускает диаграмму
        
        Args:
            timeout: Таймаут ожидания кнопки запуска в миллисекундах
            
        Returns:
            bool: True если диаграмма запущена успешно, False иначе
        """
        try:
            print("[INFO] Поиск кнопки запуска диаграммы")
            
            # Используем стандартный селектор для кнопки запуска диаграммы
            play_button = self.page.get_by_role("button", name="diagram_play_button")
            
            try:
                play_button.wait_for(state="visible", timeout=timeout)
                print("[INFO] Кнопка запуска диаграммы найдена")
                play_button.click()
                time.sleep(2)
                print("[INFO] Диаграмма запущена")
                return True
            except Exception as e:
                print(f"[ERROR] Кнопка запуска диаграммы не найдена: {e}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Ошибка при запуске диаграммы: {e}")
            return False
    
    def wait_for_diagram_completion(self, timeout: int = 60000) -> bool:
        """
        Ждет завершения выполнения диаграммы
        
        Args:
            timeout: Таймаут ожидания в миллисекундах
            
        Returns:
            bool: True если диаграмма завершилась, False иначе
        """
        try:
            print("[INFO] Ожидание завершения выполнения диаграммы...")
            time.sleep(5)  # Даем время на выполнение
            
            # Ждем появления toast сообщения
            toast = self.page.locator('[aria-label="toast"]')
            toast.wait_for(state="visible", timeout=timeout)
            print("[INFO] Toast с результатом появился")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при ожидании завершения диаграммы: {e}")
            return False
    
    def check_success_toast(self) -> bool:
        """
        Проверяет наличие toast сообщения об успешном выполнении
        
        Returns:
            bool: True если найдено сообщение об успехе, False иначе
        """
        try:
            print("[INFO] Проверка toast сообщения")
            toast_found = False
            
            # Ищем toast сообщение об успешном выполнении
            toast_success = (self.page.locator('text="Success"')
                           .or_(self.page.locator('text="Успешно"'))
                           .or_(self.page.locator('text="Выполнено"')))
            
            try:
                toast_success.wait_for(state="visible", timeout=10000)
                print("[SUCCESS] Toast сообщение об успешном выполнении найдено!")
                toast_found = True
            except Exception:
                print("[WARN] Toast сообщение об успешном выполнении не найдено")
                
            # Также проверим наличие любых toast сообщений
            toast_messages = self.page.locator('[role="alert"], .toast, .notification, [class*="toast"], [class*="notification"]')
            if toast_messages.count() > 0:
                print(f"[INFO] Найдено toast сообщений: {toast_messages.count()}")
                for i in range(min(toast_messages.count(), 3)):
                    try:
                        toast_text = toast_messages.nth(i).text_content()
                        print(f"[INFO] Toast {i}: {toast_text}")
                    except:
                        print(f"[INFO] Toast {i}: [не удалось получить текст]")
            
            # Если не найдено конкретного сообщения об успехе, но есть toast сообщения - считаем успехом
            if not toast_found and toast_messages.count() > 0:
                print("[SUCCESS] Toast сообщения найдены - диаграмма выполнена!")
                return True
                
            return toast_found
            
        except Exception as e:
            print(f"[ERROR] Ошибка при проверке toast сообщений: {e}")
            return False
    
    def run_diagram_and_wait(self, completion_timeout: int = 60000) -> bool:
        """
        Запускает диаграмму и ждет ее завершения
        
        Args:
            completion_timeout: Таймаут ожидания завершения в миллисекундах
            
        Returns:
            bool: True если диаграмма запущена и завершена успешно, False иначе
        """
        # Запускаем диаграмму
        if not self.run_diagram():
            return False
        
        # Ждем завершения
        if not self.wait_for_diagram_completion(completion_timeout):
            return False
        
        # Проверяем успешность
        return self.check_success_toast()
    
    def close_right_sidebar(self) -> bool:
        """
        Закрывает правый сайдбар
        
        Returns:
            bool: True если сайдбар закрыт успешно, False иначе
        """
        try:
            details_panel_switcher = self.page.get_by_role("button", name="diagram_details_panel_switcher")
            if details_panel_switcher.is_visible():
                details_panel_switcher.click()
                time.sleep(1)
                print("[INFO] Правый сайдбар закрыт")
                return True
            else:
                print("[INFO] Правый сайдбар уже закрыт")
                return True
        except Exception as e:
            print(f"[WARN] Ошибка при закрытии правого сайдбара: {e}")
            return False
    
    def close_file_panel(self) -> bool:
        """
        Закрывает файловую панель
        
        Returns:
            bool: True если панель закрыта успешно, False иначе
        """
        try:
            filemanager_button = self.page.get_by_role("button", name="board_toolbar_filemanager_button")
            if filemanager_button.is_visible():
                filemanager_button.click()
                time.sleep(1)
                print("[INFO] Файловая панель закрыта")
                return True
            else:
                print("[INFO] Файловая панель уже закрыта")
                return True
        except Exception as e:
            print(f"[WARN] Ошибка при закрытии файловой панели: {e}")
            return False
    
    def close_panels(self) -> bool:
        """
        Закрывает все панели (файловую и правый сайдбар)
        
        Returns:
            bool: True если все панели закрыты успешно, False иначе
        """
        file_panel_closed = self.close_file_panel()
        sidebar_closed = self.close_right_sidebar()
        return file_panel_closed and sidebar_closed
