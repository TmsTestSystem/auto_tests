from playwright.sync_api import Page
from .base_page import BasePage
import time


class DecisionTablePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    # Селекторы для таблицы решений
    DECISION_TABLE_EDITOR = '.DecisionTableTab__DecisionTableTab___mmGTJ, .DecisionTable__Main___aLCYs'
    ADD_COLUMN_BUTTON = 'text="Добавить", button:has-text("Добавить")'
    ADD_ROW_BUTTON = 'text="Добавить", button:has-text("Добавить")'
    TABLE_GRID = '.DecisionTable__Content___ZpUPd, .DecisionTableTab__TableWrapper___SeSIz'
    CELL_INPUT = '.TableColumn__Input___rGnPo, input[type="text"], [contenteditable="true"]'
    SAVE_BUTTON = 'button[aria-label*="сохранить"], button[title*="сохранить"], .save-btn'
    TABLE_ROW = '.TableRow__TableRow___0ArMJ'
    TABLE_COLUMN = '.TableColumn__TableColumn___vMhQp'
    
    # Селекторы для сайдбара
    RIGHT_SIDEBAR = '.sidebar, .right-sidebar, [data-testid="sidebar"], .Sidebar__Sidebar'
    SIDEBAR_CLOSE_BUTTON = 'button[aria-label*="закрыть"], button[title*="закрыть"], .close-btn, .sidebar-close'

    def wait_for_decision_table_editor(self):
        """Ждет появления редактора таблицы решений"""
        try:
            self.page.wait_for_selector(self.DECISION_TABLE_EDITOR, timeout=10000)
            return True
        except:
            print("[WARN] Редактор таблицы решений не найден")
            return False

    def is_decision_table_editor_visible(self):
        """Проверяет, видим ли редактор таблицы решений"""
        editor = self.page.locator(self.DECISION_TABLE_EDITOR).first
        return editor.is_visible() if editor else False

    def close_right_sidebar(self):
        """Закрывает правый сайдбар, если он открыт"""
        try:
            # Используем точный селектор для кнопки закрытия сайдбара
            close_btn = self.page.get_by_role("button", name="decision_table_details_panel_switcher").first
            if close_btn.is_visible():
                print("[INFO] Кнопка закрытия сайдбара найдена, закрываем")
                close_btn.click()
                time.sleep(1)
                print("[SUCCESS] Правый сайдбар закрыт")
                return True
            else:
                print("[INFO] Кнопка закрытия сайдбара не найдена или сайдбар уже закрыт")
                return True
        except Exception as e:
            print(f"[WARN] Не удалось закрыть правый сайдбар: {e}")
            return False

    def add_column(self, column_name: str = None):
        """Добавляет новую колонку в таблицу решений"""
        try:
            # Используем пользовательский локатор для кнопки добавления колонки
            add_column_btn = self.page.get_by_role("button", name="decision_table_add_column_button").nth(1)
            if add_column_btn.is_visible():
                add_column_btn.click()
                time.sleep(0.5)
                print(f"[SUCCESS] Колонка добавлена")
                
                # Если указано имя колонки, заполняем его
                if column_name:
                    # Ищем последнюю добавленную ячейку заголовка
                    header_cells = self.page.locator(self.TABLE_COLUMN).all()
                    if header_cells:
                        last_header = header_cells[-1]
                        last_header.click()
                        time.sleep(0.2)
                        
                        # Ищем input элемент внутри заголовка колонки
                        input_element = last_header.locator('input, [contenteditable="true"]').first
                        if input_element and input_element.is_visible():
                            input_element.fill(column_name)
                            time.sleep(0.2)
                            print(f"[SUCCESS] Имя колонки установлено: {column_name}")
                        else:
                            # Пробуем использовать keyboard input
                            last_header.press('Control+a')
                            time.sleep(0.1)
                            last_header.type(column_name)
                            time.sleep(0.2)
                            print(f"[SUCCESS] Имя колонки установлено через клавиатуру: {column_name}")
                
                return True
            else:
                print("[WARN] Кнопка добавления колонки не видима")
                return False
        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении колонки: {e}")
            return False

    def add_row(self, row_name: str = None):
        """Добавляет новую строку в таблицу решений"""
        try:
            # Используем пользовательский локатор для кнопки добавления строки
            add_row_btn = self.page.get_by_role("button", name="decision_table_add_row_button").nth(3)
            
            # Добавляем отладочную информацию
            all_row_buttons = self.page.get_by_role("button", name="decision_table_add_row_button").all()
            print(f"[DEBUG] Найдено кнопок добавления строк: {len(all_row_buttons)}")
            
            if add_row_btn.is_visible():
                add_row_btn.click()
                time.sleep(0.5)
                print(f"[SUCCESS] Строка добавлена")
                
                # Если указано имя строки, заполняем его
                if row_name:
                    # Ищем последнюю добавленную ячейку заголовка строки
                    row_header_cells = self.page.locator(self.TABLE_ROW).all()
                    if row_header_cells:
                        last_row_header = row_header_cells[-1]
                        last_row_header.click()
                        time.sleep(0.2)
                        
                        # Ищем input элемент внутри заголовка строки
                        input_element = last_row_header.locator('input, [contenteditable="true"]').first
                        if input_element and input_element.is_visible():
                            input_element.fill(row_name)
                            time.sleep(0.2)
                            print(f"[SUCCESS] Имя строки установлено: {row_name}")
                        else:
                            # Пробуем использовать keyboard input
                            last_row_header.type(row_name)
                            time.sleep(0.2)
                            print(f"[SUCCESS] Имя строки установлено через клавиатуру: {row_name}")
                
                return True
            else:
                print("[WARN] Кнопка добавления строки не видима")
                # Пробуем найти кнопку по другому селектору
                try:
                    alternative_btn = self.page.locator('button:has-text("Добавить")').nth(1)
                    if alternative_btn.is_visible():
                        alternative_btn.click()
                        time.sleep(0.5)
                        print(f"[SUCCESS] Строка добавлена через альтернативный селектор")
                        
                        # Если указано имя строки, заполняем его
                        if row_name:
                            # Ищем последнюю добавленную ячейку заголовка строки
                            row_header_cells = self.page.locator(self.TABLE_ROW).all()
                            if row_header_cells:
                                last_row_header = row_header_cells[-1]
                                last_row_header.click()
                                time.sleep(0.2)
                                
                                # Ищем input элемент внутри заголовка строки
                                input_element = last_row_header.locator('input, [contenteditable="true"]').first
                                if input_element and input_element.is_visible():
                                    input_element.fill(row_name)
                                    time.sleep(0.2)
                                    print(f"[SUCCESS] Имя строки установлено: {row_name}")
                                else:
                                    # Пробуем использовать keyboard input
                                    last_row_header.type(row_name)
                                    time.sleep(0.2)
                                    print(f"[SUCCESS] Имя строки установлено через клавиатуру: {row_name}")
                        
                        return True
                except:
                    pass
                return False
        except Exception as e:
            print(f"[ERROR] Ошибка при добавлении строки: {e}")
            return False

    def fill_cell(self, row_index: int, column_index: int, value: str):
        """Заполняет ячейку таблицы по индексам строки и колонки"""
        try:
            # Ищем все ячейки таблицы
            cells = self.page.locator(f'{self.TABLE_GRID} td, {self.TABLE_GRID} .cell').all()
            
            # Вычисляем индекс ячейки (пропускаем заголовки)
            # Предполагаем, что первая строка и первый столбец - заголовки
            if row_index > 0 and column_index > 0:
                # Пропускаем заголовки
                cell_index = (row_index - 1) * (len(cells) // 2) + (column_index - 1)
                if cell_index < len(cells):
                    cell = cells[cell_index]
                    cell.click()
                    time.sleep(0.2)
                    cell.fill(value)
                    time.sleep(0.2)
                    print(f"[SUCCESS] Ячейка [{row_index},{column_index}] заполнена значением: {value}")
                    return True
                else:
                    print(f"[WARN] Индекс ячейки [{row_index},{column_index}] выходит за пределы таблицы")
                    return False
            else:
                print(f"[WARN] Индексы строки и колонки должны быть больше 0")
                return False
        except Exception as e:
            print(f"[ERROR] Ошибка при заполнении ячейки [{row_index},{column_index}]: {e}")
            return False

    def fill_all_table_cells(self, columns: list = None, rows: list = None):
        """Заполняет все ячейки таблицы решений данными"""
        try:
            print("[INFO] Начинаем заполнение всех ячеек таблицы")
            
            # Ищем все ячейки в таблице простым способом
            table_cells = self.page.locator('input[type="text"], [contenteditable="true"]').all()
            print(f"[DEBUG] Найдено ячеек для заполнения: {len(table_cells)}")
            
            # Заполняем ячейки данными
            cell_data = [
                "Да", "Нет", "Выполнить",
                "Нет", "Да", "Пропустить",
                "Да", "Нет", "Выполнить"
            ]
            
            filled_count = 0
            
            # Заполняем каждую ячейку отдельно
            for i, cell in enumerate(table_cells):
                if i < len(cell_data):
                    try:
                        # Кликаем на ячейку
                        cell.click()
                        time.sleep(0.3)
                        
                        # Очищаем содержимое
                        cell.press('Control+a')
                        time.sleep(0.1)
                        cell.press('Delete')
                        time.sleep(0.1)
                        
                        # Вводим новое значение
                        cell.type(cell_data[i])
                        time.sleep(0.2)
                        
                        print(f"[SUCCESS] Ячейка {i+1} заполнена: {cell_data[i]}")
                        filled_count += 1
                        
                        # Нажимаем Enter для подтверждения
                        cell.press('Enter')
                        time.sleep(0.2)
                        
                    except Exception as e:
                        print(f"[WARN] Не удалось заполнить ячейку {i+1}: {e}")
                else:
                    break
            
            print(f"[SUCCESS] Заполнено {filled_count} ячеек")
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка при заполнении ячеек таблицы: {e}")
            return False

    def get_table_structure(self):
        """Получает структуру таблицы (количество строк и колонок)"""
        try:
            # Ищем заголовки колонок
            column_headers = self.page.locator(self.TABLE_COLUMN).all()
            # Ищем заголовки строк
            row_headers = self.page.locator(self.TABLE_ROW).all()
            
            columns_count = len(column_headers)
            rows_count = len(row_headers)
            
            print(f"[INFO] Структура таблицы: {rows_count} строк, {columns_count} колонок")
            return {
                'rows': rows_count,
                'columns': columns_count,
                'row_headers': [h.inner_text() for h in row_headers],
                'column_headers': [h.inner_text() for h in column_headers]
            }
        except Exception as e:
            print(f"[ERROR] Ошибка при получении структуры таблицы: {e}")
            return None

    def save_decision_table(self):
        """Сохраняет таблицу решений"""
        try:
            save_btn = self.page.locator(self.SAVE_BUTTON).first
            if save_btn.is_visible():
                save_btn.click()
                time.sleep(1)
                print("[SUCCESS] Таблица решений сохранена")
                return True
            else:
                # Пробуем использовать горячие клавиши
                self.page.keyboard.press('Control+s')
                time.sleep(1)
                print("[SUCCESS] Таблица решений сохранена через горячие клавиши")
                return True
        except Exception as e:
            print(f"[ERROR] Ошибка при сохранении таблицы решений: {e}")
            return False

    def create_basic_decision_table(self, columns: list = None, rows: list = None):
        """Создает базовую таблицу решений с указанными колонками и строками"""
        print("[INFO] Создание базовой таблицы решений")
        
        # Ждем появления редактора
        if not self.wait_for_decision_table_editor():
            return False
        
        # Закрываем сайдбар один раз в начале
        print("[INFO] Закрываем сайдбар перед началом работы с таблицей")
        self.close_right_sidebar()
        
        # Добавляем колонки
        if columns:
            for i, column_name in enumerate(columns):
                if not self.add_column(column_name):
                    print(f"[WARN] Не удалось добавить колонку: {column_name}")
        
        # Добавляем строки
        if rows:
            for i, row_name in enumerate(rows):
                if not self.add_row(row_name):
                    print(f"[WARN] Не удалось добавить строку: {row_name}")
        
        # Получаем структуру таблицы
        structure = self.get_table_structure()
        if structure:
            print(f"[SUCCESS] Таблица решений создана: {structure['rows']} строк, {structure['columns']} колонок")
            
            # Заполняем все ячейки таблицы
            print("[INFO] Заполняем все ячейки таблицы данными")
            self.fill_all_table_cells(columns, rows)
            
            return True
        else:
            print("[WARN] Не удалось получить структуру таблицы")
            return False 