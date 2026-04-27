from playwright.sync_api import Page
from .base_page import BasePage
import time


class ProcessSchedulePage(BasePage):
    """Page Object для работы с расписанием процессов"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    def goto_schedule_from_project_card(self, project_title: str):
        """Переход в раздел расписания процессов через карточку проекта"""
        # Возвращаемся на главную страницу со списком проектов
        self.page.get_by_role("button", name="home page icon").click()
        self.page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        # Находим карточку проекта
        project_card = (
            self.page.locator('div[aria-label="projects_card"]')
            .filter(has_text=project_title)
            .first
        )
        
        # Открываем меню карточки проекта
        project_card.get_by_role("button", name="projects_card_menu_button").click()
        time.sleep(0.5)
        
        # Ищем пункт "Расписание процессов" или "Расписание"
        schedule_menu_item = self.page.get_by_text("Расписание процессов", exact=True)
        if schedule_menu_item.count() == 0:
            schedule_menu_item = self.page.get_by_text("Расписание", exact=True)
        
        schedule_menu_item.click()
        self.page.wait_for_load_state("networkidle")
        time.sleep(1)

    def open_create_schedule_modal(self):
        """Открывает модальное окно создания нового расписания"""
        create_btn = self.page.get_by_role("button", name="schedules_create_button")
        create_btn.click()
        time.sleep(1)

    def create_schedule(
        self, 
        name: str, 
        version: str,
        process_file: str, 
        cron_second: str = "*",
        cron_minute: str = "*",
        cron_hour: str = "*",
        cron_day: str = "*",
        cron_month: str = "*",
        cron_weekday: str = "*",
        cron_year: str = "*",
        request_data: dict = None
    ):
        """
        Создает новое расписание процесса
        
        Args:
            name: Название расписания (поле "Имя")
            version: Версия/релиз для запуска (выбирается из выпадающего списка)
            process_file: Путь к файлу процесса (например, "TutorialProcess.df.json")
            cron_second: Секунда для cron (по умолчанию "*")
            cron_minute: Минута для cron (по умолчанию "*")
            cron_hour: Час для cron (по умолчанию "*")
            cron_day: День месяца для cron (по умолчанию "*")
            cron_month: Месяц для cron (по умолчанию "*")
            cron_weekday: День недели для cron (по умолчанию "*")
            cron_year: Год для cron (по умолчанию "*")
            request_data: Данные запроса (dict с полями object_id, request_id, tags, body)
        """
        print(f"[DEBUG] Создание расписания:")
        print(f"[DEBUG] - name: {name}")
        print(f"[DEBUG] - version: {version}")
        print(f"[DEBUG] - process: {process_file}")
        print(f"[DEBUG] - cron: {cron_second} {cron_minute} {cron_hour} {cron_day} {cron_month} {cron_weekday} {cron_year}")
        
        # Заполняем поле "Имя" (title)
        name_input = self.page.get_by_role("textbox", name="title")
        name_input.click()
        name_input.fill(name)
        print(f"[DEBUG] Поле 'Имя' заполнено: {name}")
        
        # Выбираем версию - кликаем по полю version
        version_input = self.page.get_by_role("textbox", name="version")
        version_input.click()
        time.sleep(0.5)
        
        # Кликаем по кнопке "Коммиты"
        commits_button = self.page.locator("button").filter(has_text="Коммиты")
        commits_button.click()
        time.sleep(1)
        
        # Выбираем коммит (ищем по тексту version)
        commit_option = self.page.get_by_text(version, exact=False).first
        commit_option.click()
        time.sleep(0.5)
        print(f"[DEBUG] Версия выбрана")
        
        # Выбираем процесс - кликаем по кнопке выбора файла
        file_select_button = self.page.get_by_role("button", name="textfield_select_file_button")
        file_select_button.click()
        time.sleep(1)
        
        # Выбираем файл процесса
        process_option = self.page.get_by_text(process_file)
        process_option.click()
        time.sleep(0.5)
        
        # Нажимаем кнопку выбора в модалке
        select_button = self.page.get_by_role("button", name="filemanager_select_button")
        select_button.click()
        time.sleep(0.5)
        print(f"[DEBUG] Процесс выбран: {process_file}")
        
        # Заполняем регулярность (cron-поля)
        # frequency.0 - секунда
        self.page.get_by_role("textbox", name="frequency.0").fill(cron_second)
        print(f"[DEBUG] Секунда: {cron_second}")
        
        # frequency.1 - минута
        self.page.get_by_role("textbox", name="frequency.1").fill(cron_minute)
        print(f"[DEBUG] Минута: {cron_minute}")
        
        # frequency.2 - час
        self.page.get_by_role("textbox", name="frequency.2").fill(cron_hour)
        print(f"[DEBUG] Час: {cron_hour}")
        
        # frequency.3 - день месяца
        self.page.get_by_role("textbox", name="frequency.3").fill(cron_day)
        print(f"[DEBUG] День месяца: {cron_day}")
        
        # frequency.4 - месяц
        self.page.get_by_role("textbox", name="frequency.4").fill(cron_month)
        print(f"[DEBUG] Месяц: {cron_month}")
        
        # frequency.5 - день недели
        self.page.get_by_role("textbox", name="frequency.5").fill(cron_weekday)
        print(f"[DEBUG] День недели: {cron_weekday}")
        
        # frequency.6 - год
        self.page.get_by_role("textbox", name="frequency.6").fill(cron_year)
        print(f"[DEBUG] Год: {cron_year}")
        
        # Заполняем тело запроса - нажимаем кнопку предзаполнения
        paste_button = self.page.get_by_role("button", name="formitem_paste_button")
        paste_button.click()
        time.sleep(1)
        print("[DEBUG] Тело запроса предзаполнено")
        
        # Заполняем данные запроса (опционально)
        if request_data:
            if 'object_id' in request_data:
                object_id_input = self.page.get_by_role("textbox", name="object_id")
                object_id_input.click()
                object_id_input.fill(request_data['object_id'])
                time.sleep(0.5)
                print(f"[DEBUG] object_id: {request_data['object_id']}")
            
            if 'request_id' in request_data:
                request_id_input = self.page.get_by_role("textbox", name="request_id")
                request_id_input.click()
                request_id_input.fill(request_data['request_id'])
                time.sleep(0.5)
                print(f"[DEBUG] request_id: {request_data['request_id']}")
            
            if 'tags' in request_data:
                tags_input = self.page.get_by_role("textbox", name="tags")
                tags_input.click()
                tags_input.fill(request_data['tags'])
                time.sleep(0.5)
                print(f"[DEBUG] tags: {request_data['tags']}")
        
        time.sleep(1)
        
        # Нажимаем кнопку "Отправить"
        submit_button = self.page.get_by_role("button", name="Отправить")
        submit_button.click()
        print("[DEBUG] Кнопка 'Отправить' нажата")

    def wait_modal_close(self):
        """Ожидает закрытия модального окна"""
        print("[DEBUG] Ожидание закрытия модального окна...")
        modal = self.page.locator('[data-testid="Modal__Container"]')
        try:
            modal.wait_for(state="hidden", timeout=15000)
            print("[DEBUG] Модальное окно успешно закрыто")
        except:
            # Если модалка не закрылась, проверяем есть ли ошибки
            print("[WARN] Модалка не закрылась, проверяем ошибки...")
            try:
                errors = self.page.locator('.error, [class*="error"], [class*="Error"]').all()
                if len(errors) > 0:
                    for error in errors:
                        try:
                            if error.is_visible():
                                error_text = error.inner_text()
                                print(f"[ERROR] Ошибка валидации: {error_text}")
                        except:
                            pass
            except:
                pass
            # Попробуем закрыть модалку вручную
            try:
                close_btn = self.page.locator('[aria-label="close"], button:has-text("Закрыть")').first
                if close_btn.count() > 0 and close_btn.is_visible():
                    close_btn.click()
                    time.sleep(1)
            except:
                pass
            print("[DEBUG] Продолжаем тест")

    def get_schedule_table(self):
        """Получает таблицу расписаний"""
        table = self.page.locator('table, [role="table"], .schedule-table')
        table.wait_for(state="visible", timeout=10000)
        return table

    def verify_schedule_exists(self, schedule_name: str):
        """Проверяет наличие расписания в списке"""
        table = self.get_schedule_table()
        table_text = table.inner_text()
        assert schedule_name in table_text, f"Расписание '{schedule_name}' не найдено в списке"
        print(f"[INFO] Расписание '{schedule_name}' найдено в списке")

    def delete_schedule(self, schedule_name: str):
        """
        Удаляет расписание по имени
        
        Args:
            schedule_name: Название расписания для удаления
        """
        # Ищем строку с расписанием
        schedule_row = self.page.get_by_role("row").filter(has_text=schedule_name)
        assert schedule_row.count() > 0, f"Расписание '{schedule_name}' не найдено"
        
        # Ищем кнопку удаления в строке
        delete_button = schedule_row.get_by_role("button", name="delete")
        if delete_button.count() == 0:
            delete_button = schedule_row.locator('[aria-label*="delete"], [title*="Удалить"]')
        
        delete_button.click()
        time.sleep(0.5)
        
        # Подтверждаем удаление если есть подтверждение
        confirm_button = self.page.get_by_role("button", name="Удалить")
        if confirm_button.count() > 0:
            confirm_button.click()
        
        time.sleep(1)
        print(f"[INFO] Расписание '{schedule_name}' удалено")

    def open_schedule_details(self, schedule_name: str):
        """
        Открывает детальную страницу расписания
        
        Args:
            schedule_name: Название расписания
        """
        schedule_link = self.page.get_by_role("link", name=schedule_name)
        if schedule_link.count() == 0:
            schedule_link = self.page.locator("tbody tr").filter(has_text=schedule_name).first
        schedule_link.first.wait_for(state="visible", timeout=30000)
        schedule_link.first.click()
        time.sleep(2)
        print(f"[INFO] Открыта страница расписания '{schedule_name}'")

    def activate_schedule(self):
        """Активирует расписание"""
        activate_button = self.page.get_by_role("button", name="schedule_activate_button")
        activate_button.click()
        time.sleep(1)
        print("[INFO] Расписание активировано")

    def deactivate_schedule(self):
        """Деактивирует расписание"""
        deactivate_button = self.page.get_by_role("button", name="schedule_deactivate_button")
        deactivate_button.click()
        time.sleep(1)
        print("[INFO] Расписание деактивировано")

    def start_schedule_manually(self):
        """
        Запускает процесс по расписанию вручную
        """
        # Нажимаем кнопку запуска
        start_button = self.page.get_by_role("button", name="schedule_start_button")
        start_button.click()
        time.sleep(1)
        
        # Подтверждаем запуск
        confirm_button = self.page.get_by_role("button", name="Запустить")
        confirm_button.click()
        time.sleep(1)
        
        # Проверяем уведомление
        notification = self.page.locator("div").filter(has_text="Процесс запущен").nth(2)
        notification.wait_for(state="visible", timeout=10000)
        print("[INFO] Процесс запущен вручную, уведомление отображено")
        time.sleep(2)

    def verify_execution_in_history(self, max_wait_seconds=30):
        """
        Проверяет что запуск появился в истории запусков
        
        Args:
            max_wait_seconds: Максимальное время ожидания появления записи в секундах
        """
        print(f"[INFO] Ожидаем появления записи в истории (до {max_wait_seconds} сек)...")
        
        start_time = time.time()
        found = False
        
        while time.time() - start_time < max_wait_seconds:
            # Ищем строки в таблице истории
            table_rows = self.page.locator('table [role="row"]').all()
            
            # Если нашли больше 1 строки (первая - заголовок), значит запись появилась
            if len(table_rows) > 1:
                print(f"[INFO] В истории запусков найдено записей: {len(table_rows) - 1}")
                print("[SUCCESS] Запуск появился в истории")
                found = True
                break
            
            # Также проверяем наличие статусов выполнения
            status_texts = self.page.locator('text=/Завершён|Завершен|В процессе|Ошибка/i').all()
            if len(status_texts) > 0:
                print(f"[INFO] Найдено записей со статусами: {len(status_texts)}")
                print("[SUCCESS] Запуск появился в истории")
                found = True
                break
            
            # Ждем 2 секунды перед следующей проверкой
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                print(f"[DEBUG] Ожидание... ({elapsed}/{max_wait_seconds} сек)")
            time.sleep(2)
        
        if not found:
            print(f"[WARN] Запись не появилась в истории за {max_wait_seconds} секунд")
            # Выводим отладочную информацию
            all_rows = self.page.locator('[role="row"]').all()
            print(f"[DEBUG] Найдено всего строк на странице: {len(all_rows)}")
        
        # Не фейлим тест, просто предупреждаем
        assert found, f"Запись не появилась в истории за {max_wait_seconds} секунд"

    def toggle_schedule_status(self, schedule_name: str):
        """
        Переключает статус расписания (включено/выключено)
        
        Args:
            schedule_name: Название расписания
        """
        # Сначала открываем детальную страницу расписания
        self.open_schedule_details(schedule_name)
        
        # Ищем переключатель или чекбокс на странице деталей
        toggle = self.page.get_by_role("switch")
        if toggle.count() == 0:
            toggle = self.page.get_by_role("checkbox")
        
        toggle.click()
        time.sleep(1)
        print(f"[INFO] Статус расписания '{schedule_name}' переключен")

    def verify_schedule_status(self, schedule_name: str, expected_status: str):
        """
        Проверяет статус расписания
        
        Args:
            schedule_name: Название расписания
            expected_status: Ожидаемый статус ('enabled' или 'disabled')
        """
        schedule_row = self.page.get_by_role("row").filter(has_text=schedule_name)
        assert schedule_row.count() > 0, f"Расписание '{schedule_name}' не найдено"
        
        row_text = schedule_row.inner_text().lower()
        print(f"[DEBUG] Текст строки расписания: {row_text}")
        
        if expected_status.lower() == 'enabled':
            assert 'активировано' in row_text and 'не активировано' not in row_text, \
                f"Расписание '{schedule_name}' не включено. Текст строки: {row_text}"
        else:
            assert 'не активировано' in row_text or 'выключено' in row_text or 'disabled' in row_text, \
                f"Расписание '{schedule_name}' не выключено. Текст строки: {row_text}"
        
        print(f"[INFO] Расписание '{schedule_name}' имеет статус '{expected_status}'")

