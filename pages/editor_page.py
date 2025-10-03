from playwright.sync_api import Page
from .base_page import BasePage
import time

class EditorPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    # Селекторы для редакторов
    MONACO_EDITOR = 'textarea.inputarea'
    SAVE_BUTTON = 'button[title*="Сохранить"], button[title*="Save"], .save-button, [aria-label*="сохранить"]'
    ALL_TEXTAREAS = 'textarea'

    def find_monaco_editor(self):
        """Находит Monaco Editor на странице"""
        return self.page.locator(self.MONACO_EDITOR).first

    def is_editor_visible(self):
        """Проверяет, видим ли редактор"""
        editor = self.find_monaco_editor()
        return editor.is_visible() if editor else False

    def fill_editor_content(self, content: str):
        """Заполняет редактор содержимым"""
        editor = self.find_monaco_editor()
        if editor and editor.is_visible():
            # Просто вставляем код, Monaco Editor сам обработает содержимое
            editor.fill(content)
            return True
        return False

    def get_editor_content(self):
        """Получает содержимое редактора"""
        editor = self.find_monaco_editor()
        if editor and editor.is_visible():
            return editor.input_value()
        return ""

    def verify_content_contains(self, expected_text: str):
        """Проверяет, содержит ли редактор ожидаемый текст"""
        content = self.get_editor_content()
        return expected_text in content

    def save_file(self):
        """Сохраняет файл через кнопку или горячие клавиши"""
        try:
            # Попробуем найти кнопку сохранения
            save_button = self.page.locator(self.SAVE_BUTTON).first
            if save_button.is_visible():
                save_button.click()
                time.sleep(0.5)
                return True
            else:
                # Если кнопка сохранения не найдена, используем горячие клавиши
                self.page.keyboard.press('Control+s')
                time.sleep(0.5)
                return True
        except Exception as e:
            print(f"[WARN] Не удалось сохранить файл: {e}")
            return False

    def get_all_textareas_info(self):
        """Получает информацию о всех textarea на странице для диагностики"""
        all_textareas = self.page.locator(self.ALL_TEXTAREAS).all()
        textareas_info = []
        
        for i, ta in enumerate(all_textareas):
            try:
                readonly = ta.get_attribute('readonly')
                name = ta.get_attribute('name')
                aria_label = ta.get_attribute('aria-label')
                class_name = ta.get_attribute('class')
                textareas_info.append({
                    'index': i,
                    'readonly': readonly,
                    'name': name,
                    'aria_label': aria_label,
                    'class': class_name
                })
            except:
                textareas_info.append({
                    'index': i,
                    'error': 'не удалось получить атрибуты'
                })
        
        return textareas_info

    def fill_and_save_python_script(self, script_name: str, python_code: str):
        """Полный цикл заполнения и сохранения Python скрипта"""
        # Ждем, пока файл откроется в редакторе
        time.sleep(2)
        
        # Заполняем редактор
        if self.fill_editor_content(python_code):
            print(f"[CODE] Python код вставлен в редактор")
            
            # Ждем немного для обработки
            time.sleep(1)
            
            # Проверяем, что код действительно вставлен
            content = self.get_editor_content()
            print(f"[DEBUG] Полное содержимое редактора:")
            print(f"[DEBUG] {repr(content)}")
            
            if self.verify_content_contains("def main():"):
                print(f"[VERIFY] Код успешно вставлен в редактор")
            else:
                print(f"[WARN] Код может быть не полностью вставлен")
                print(f"[DEBUG] Содержимое редактора: {content[:100]}...")
            
            # Сохраняем файл
            if self.save_file():
                print(f"[SAVE] Файл сохранен")
                return True
            else:
                print(f"[WARN] Не удалось сохранить файл")
                return False
        else:
            print(f"[WARN] Monaco Editor не найден или не видим")
            return False 