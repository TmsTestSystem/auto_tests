from playwright.sync_api import Page
from .base_page import BasePage
import time
import re


class ReleasePage(BasePage):
    """Page Object для работы с релизами"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page = page

    def goto_releases_from_project_card(self, project_title: str):
        """Переход в раздел релизов через карточку проекта"""
        self.page.get_by_role("button", name="home page icon").click()
        self.page.wait_for_load_state("networkidle")
        project_card = (
            self.page.locator('div[aria-label="projects_card"]').filter(has_text=project_title).first
        )
        project_card.get_by_role("button", name="projects_card_menu_button").click()
        self.page.get_by_text("Релизы", exact=True).click()
        self.page.wait_for_load_state("networkidle")

    def create_release(self, title: str, alias: str, commit_message: str):
        """Создаёт новый релиз с указанным коммитом"""
        self.page.get_by_role("button", name="release_create_button").click()
        self.page.get_by_role("textbox", name="title").click()
        self.page.get_by_role("textbox", name="title").fill(title)
        self.page.get_by_role("textbox", name="alias").click()
        self.page.get_by_role("textbox", name="alias").fill(alias)
        self.page.locator("label").nth(2).click()
        self.page.locator("button").filter(has_text="Коммиты").click()
        commit_entry = self.page.get_by_text(commit_message, exact=True)
        commit_entry.wait_for(state="visible", timeout=10000)
        commit_entry.click()
        send_button = self.page.get_by_role("button", name="Отправить")
        send_button.wait_for(state="visible", timeout=5000)
        send_button.click(force=True)
        self.page.wait_for_load_state("networkidle")

    def open_release_by_title(self, release_title: str):
        """Открывает релиз по названию из списка релизов"""
        release_link = self.page.get_by_role("link", name=release_title)
        release_link.wait_for(state="visible", timeout=10000)
        release_link.click()
        self.page.wait_for_load_state("networkidle")

    def open_release_from_table(self):
        """Открывает первый релиз из таблицы (по XPath)"""
        release_link = self.page.locator('xpath=//*[@id="root"]/div[2]/section/div[2]/div[1]/div/table/tbody/tr/td[1]/a')
        release_link.first.wait_for(state="visible", timeout=15000)
        release_href = release_link.first.get_attribute("href")
        release_link.first.click()
        if release_href:
            self.page.wait_for_url(re.compile(release_href), timeout=10000)
        else:
            self.page.wait_for_url(re.compile(r"/setup/releases/\d+"), timeout=10000)
        self.page.wait_for_load_state("networkidle")

    def validate_release_data(self, release_title: str, release_alias: str, endpoint_alias: str, expected_status: str = "Черновик"):
        """Валидирует данные релиза на странице"""
        info_table = self.page.locator('table.AdminPanel__CardInfoVertical___EsIJ4').first
        info_table.wait_for(state="visible", timeout=10000)
        table_rows = info_table.locator('tr')
        
        name_row = table_rows.filter(has_text="Имя").first.inner_text()
        assert release_title in name_row, "Имя релиза не отображается"
        
        status_row = table_rows.filter(has_text="Статус").first.inner_text()
        assert expected_status in status_row, f"Статус релиза должен быть '{expected_status}'"
        
        alias_row = table_rows.filter(has_text="Алиас").first.inner_text()
        assert release_alias in alias_row, "Алиас релиза не отображается"

        endpoints_table = self.page.locator('section:has-text("Эндпоинты") tbody.Table__Body___I87b4')
        endpoints_table.wait_for(state="visible", timeout=10000)
        table_text = endpoints_table.inner_text()
        assert endpoint_alias in table_text, "Алиас эндпоинта отсутствует"
        assert "TutorialProcess.df.json" in table_text, "Процесс TutorialProcess.df.json не привязан"

    def publish_release(self):
        """Публикует релиз"""
        self.page.get_by_role("button", name="release_publish_button").click()
        # Даём UI время обновить состояние; текст уведомления может отличаться между стендами,
        # поэтому не проверяем конкретную строку здесь. Корректность публикации
        # дополнительно валидируется через API и журнал процессов в самом тесте.
        self.page.wait_for_timeout(2000)

    def unpublish_release(self):
        """Снимает релиз с публикации"""
        self.page.get_by_role("button", name="release_unpublish_button").click()
        self.page.get_by_role("button", name="Снять с публикации").click()
        self.page.wait_for_timeout(2000)

    def change_release_version(self, version_label: str = "Initial"):
        """Изменяет версию релиза"""
        # Сначала снимаем с публикации, если релиз опубликован
        try:
            unpublish_btn = self.page.get_by_role("button", name="release_unpublish_button")
            if unpublish_btn.is_enabled():
                unpublish_btn.click()
                self.page.get_by_role("button", name="Снять с публикации").click()
                self.page.wait_for_timeout(2000)
        except Exception:
            pass  # Релиз уже в черновике
        
        self.page.get_by_role("button", name="release_change_button").click()
        self.page.get_by_role("textbox", name="version").click()
        version_commit = self.page.get_by_label(version_label).first
        version_commit.wait_for(state="visible", timeout=10000)
        version_commit.click()
        self.page.get_by_role("button", name="Отправить").click()
        self.page.wait_for_timeout(2000)

    def delete_release(self):
        """Удаляет релиз"""
        self.page.get_by_role("button", name="release_delete_button").click()
        self.page.get_by_role("button", name="Удалить").click()
        self.page.wait_for_timeout(2000)

    def goto_releases_link(self):
        """Переход в раздел релизов через ссылку в навигации"""
        self.page.get_by_role("link", name="Релизы").click()
        self.page.wait_for_load_state("networkidle")
