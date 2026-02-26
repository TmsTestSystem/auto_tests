from playwright.sync_api import Page
from .base_page import BasePage
import os
import time
import re

class ProjectPage(BasePage):
    CREATE_BUTTON = 'button[aria-label="projects_create_button"]'
    MODAL_FORM = 'form'
    MODAL_BACKDROP = '.Modal__Backdrop'
    PROJECT_LIST = '[data-testid="project-list"]'
    PROJECT_ROW = 'a[href^="/projects/"]'
    SUBMIT_BUTTON = 'button[aria-label="Отправить"]'

    def __init__(self, page: Page):
        super().__init__(page)
        # Главная страница уже является списком проектов, перехода на /projects не требуется
        raw_base = (os.getenv("BASE_URL") or "").strip()
        if raw_base and not raw_base.startswith(("http://", "https://")):
            raw_base = "https://" + raw_base
        base_url = raw_base.rstrip("/")
        self.projects_url = base_url or ""

    def goto(self):
        self.page.goto(self.projects_url)
        self.page.wait_for_load_state('networkidle')

    def open_create_project_modal(self):
        # Новый диалог создаётся кнопкой с aria-label / accessible name "projects_create_button"
        btn = self.page.get_by_role("button", name="projects_create_button")
        btn.wait_for(state="visible", timeout=15000)
        btn.click()
        self.page.wait_for_selector(self.MODAL_FORM, timeout=10000)

    def create_project(self, title: str, code: str, git: str, default_branch: str):
        print(f"[DEBUG] Заполнение модального окна создания проекта:")
        print(f"[DEBUG] - title: {title}")
        print(f"[DEBUG] - code: {code}")
        print(f"[DEBUG] - git: {git}")
        print(f"[DEBUG] - default_branch: {default_branch}")
        
        # Новый UI создаёт проект через форму project_json.*
        try:
            # Title
            title_field = self.page.get_by_role("textbox", name="project_json.title")
            title_field.wait_for(state="visible", timeout=10000)
            title_field.click()
            title_field.fill(title)
            print(f"[DEBUG] Поле project_json.title заполнено: {title}")
            
            # Code
            code_field = self.page.get_by_role("textbox", name="project_json.code")
            code_field.wait_for(state="visible", timeout=10000)
            code_field.click()
            code_field.fill(code)
            print(f"[DEBUG] Поле project_json.code заполнено: {code}")
            
            # Description (опционально)
            try:
                desc_field = self.page.get_by_role("textbox", name="project_json.description")
                desc_field.wait_for(state="visible", timeout=5000)
                desc_field.click()
                desc_field.fill(f"Автотестовый проект {title}")
                print("[DEBUG] Поле project_json.description заполнено")
            except Exception:
                print("[WARN] Поле project_json.description не найдено, пропускаем")

            # Тип проекта: выбираем вариант "Пустой"
            try:
                empty_option = self.page.locator("div").filter(has_text=re.compile(r"^Пустой$"))
                empty_option.first.click()
                print("[DEBUG] Выбран тип проекта 'Пустой'")
            except Exception:
                print("[WARN] Не удалось выбрать тип проекта 'Пустой'")

            # Отмечаем чекбокс "Преобразовать в git", чтобы проект поддерживал git-операции
            try:
                git_checkbox = (
                    self.page.locator("label")
                    .filter(has_text=re.compile(r"Преобразовать в git"))
                    .locator("div")
                )
                git_checkbox.first.click()
                print("[DEBUG] Установлен чекбокс 'Преобразовать в git'")
            except Exception:
                print("[WARN] Не удалось установить чекбокс 'Преобразовать в git'")

            # Отправка формы
            submit_btn = self.page.get_by_role("button", name="Отправить")
            submit_btn.wait_for(state="visible", timeout=10000)
            submit_btn.click()
            print("[DEBUG] Кнопка 'Отправить' нажата")
            
        except Exception as e:
            print(f"[ERROR] Ошибка при заполнении модального окна: {e}")
            # Делаем скриншот для отладки
            self.page.screenshot(path="screenshots/modal_filling_error.png")
            raise

    def wait_modal_close(self):
        print("[DEBUG] Ожидание закрытия модального окна...")
        try:
            self.page.wait_for_selector(self.MODAL_FORM, state='detached', timeout=30000)
            print("[DEBUG] Модальное окно успешно закрыто")
        except Exception as e:
            print(f"[ERROR] Модальное окно не закрылось: {e}")
            # Делаем скриншот для отладки
            self.page.screenshot(path="screenshots/modal_timeout.png")
            raise

    def import_project(self):
        """
        Обязательный шаг импорта проекта после создания.
        Создает ZIP архив из папки project_for_tests и импортирует его через файловую панель.
        """
        try:
            from utils.project_zip_utils import create_project_zip, get_project_folder_path, cleanup_temp_zip
            from pages.file_panel_page import FilePanelPage
            import tempfile
            import os
            
            print("[PROJECT_IMPORT] Начинаю импорт проекта")
            
            # Получаем путь к папке project_for_tests
            project_folder_path = get_project_folder_path()
            
            # Создаем временный ZIP архив (уникальное имя, чтобы не ловить WinError 32)
            zip_path = create_project_zip(project_folder_path)
            
            try:
                # Импортируем ZIP архив
                file_panel = FilePanelPage(self.page)
                file_panel.import_project_zip(zip_path)
                
                print("[PROJECT_IMPORT] Импорт проекта успешно завершен")
                
            finally:
                # Удаляем временный ZIP архив
                cleanup_temp_zip(zip_path)
                
        except Exception as e:
            print(f"[ERROR] Ошибка при импорте проекта: {e}")
            raise

    def find_project_in_list(self, title: str):
        self.page.wait_for_selector('div[aria-label="projects_card"]', timeout=10000)
        cards = self.page.query_selector_all('div[aria-label="projects_card"]')
        for card in cards:
            title_div = card.query_selector('div[aria-label="projects_card_title"]')
            if title_div and title_div.inner_text().strip() == title:
                link = card.query_selector('a[aria-label="projects_card_link"]')
                return link
        return None

    def goto_project(self, code: str):
        # Проверяем, находимся ли мы уже в нужном проекте
        current_url = self.page.url
        if f'/projects/{code}/' in current_url or f'/projects/{code}?' in current_url:
            print(f"[PROJECT_PAGE] Уже находимся в проекте {code}")
            return True
        
        # Обновляем страницу проектов и пытаемся найти ссылку, содержащую код
        self.goto()
        try:
            self.page.wait_for_selector(self.PROJECT_ROW, timeout=15000)
        except Exception:
            pass

        for _ in range(20):  # до ~10 секунд с полсекундным ожиданием
            links = self.page.query_selector_all(self.PROJECT_ROW)
            for link in links:
                href = link.get_attribute('href')
                if href and code in href:
                    link.click()
                    self.page.wait_for_load_state('networkidle')
                    return True
            # Если не нашли — обновим список и попробуем ещё раз
            try:
                self.page.reload()
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def goto_first_available_project(self, timeout=15000):
        self.page.wait_for_selector('div[aria-label="projects_card"]', timeout=timeout)
        cards = self.page.query_selector_all('div[aria-label="projects_card"]')
        if not cards:
            raise Exception('Нет доступных проектов!')
        first_card = cards[0]
        link = first_card.query_selector('a[aria-label="projects_card_link"]')
        if not link:
            raise Exception('Не найдена ссылка на проект!')
        link.click()
        self.page.wait_for_load_state('networkidle')

    def check_required_buttons(self, required_aria_labels):
        for label in required_aria_labels:
            assert self.page.is_visible(f'button[aria-label="{label}"]'), f'Кнопка с aria-label="{label}" не найдена!' 

    def wait_for_toolbar_buttons(self, toolbar_labels, timeout=20000):
        found_labels = set()
        for _ in range(int(timeout / 500)):
            buttons = self.page.query_selector_all('button[aria-label]')
            found_labels = set(btn.get_attribute('aria-label') for btn in buttons if btn.get_attribute('aria-label') in toolbar_labels)
            if found_labels == set(toolbar_labels):
                break
            time.sleep(0.5)
        return found_labels

    def get_file_sidebar_buttons(self):
        return self.page.query_selector_all('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]') 

    def open_file_panel(self):
        from pages.file_panel_page import FilePanelPage
        file_panel = FilePanelPage(self.page)
        file_panel.open_file_panel() 

    def is_project_present(self, code: str, wait_seconds: int = 15) -> bool:
        """Проверить, что проект с заданным кодом появился в списке (без перехода).
        Делает начальный переход на страницу проектов и периодически обновляет её.
        """
        self.goto()
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            try:
                self.page.wait_for_selector(self.PROJECT_ROW, timeout=3000)
            except Exception:
                pass
            links = self.page.query_selector_all(self.PROJECT_ROW)
            for link in links:
                href = link.get_attribute('href')
                if href and code in href:
                    return True
            try:
                self.page.reload()
            except Exception:
                pass
            time.sleep(0.5)
        return False
