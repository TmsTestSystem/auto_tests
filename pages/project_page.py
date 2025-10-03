from playwright.sync_api import Page
from .base_page import BasePage
import os
import time

class ProjectPage(BasePage):
    CREATE_BUTTON = 'button:has-text("Создать проект")'
    MODAL_FORM = 'form'
    MODAL_BACKDROP = '.Modal__Backdrop'
    PROJECT_LIST = '[data-testid="project-list"]'
    PROJECT_ROW = 'a[href^="/projects/"]'
    SUBMIT_BUTTON = 'button[aria-label="Отправить"]'

    def __init__(self, page: Page):
        super().__init__(page)
        # Главная страница уже является списком проектов, перехода на /projects не требуется
        self.projects_url = f"{os.getenv('BASE_URL')}"

    def goto(self):
        self.page.goto(self.projects_url)
        self.page.wait_for_load_state('networkidle')

    def open_create_project_modal(self):
        self.page.wait_for_selector(self.CREATE_BUTTON, timeout=15000)
        self.page.click(self.CREATE_BUTTON)
        self.page.wait_for_selector(self.MODAL_FORM, timeout=10000)

    def create_project(self, title: str, code: str, git: str, default_branch: str):
        for label, value in [
            ('title', title),
            ('code', code),
            ('git', git),
            ('default_branch', default_branch),
        ]:
            self.page.wait_for_selector(f"input[aria-label='{label}']", timeout=10000)
            self.page.fill(f"input[aria-label='{label}']", value)
        self.page.click(self.SUBMIT_BUTTON)

    def wait_modal_close(self):
        self.page.wait_for_selector(self.MODAL_FORM, state='detached', timeout=15000)

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
