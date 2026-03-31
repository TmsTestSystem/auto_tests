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
        # Не завязываемся на CSS Modules (классы на фронте меняются или переименовываются).
        self.page.wait_for_url(re.compile(r"/projects/[^/]+/setup/releases/\d+"), timeout=20000)
        self.page.wait_for_load_state("networkidle")

        # Контент карточки часто вне <main> или в отдельных блоках — ждём появления текста в DOM.
        title_pat = re.compile(re.escape(release_title))
        self.page.get_by_text(title_pat).first.wait_for(state="visible", timeout=20000)
        self.page.get_by_text(re.escape(release_alias)).first.wait_for(state="visible", timeout=20000)

        body_text = self.page.locator("body").inner_text()
        assert expected_status.lower() in body_text.lower(), (
            f"Статус релиза должен содержать '{expected_status}' (без учёта регистра), фрагмент: {body_text[:800]!r}"
        )

        ep_sections = self.page.locator("section").filter(has_text="Эндпоинты")
        if ep_sections.count() > 0:
            endpoints_table = ep_sections.first.locator("tbody").first
        else:
            endpoints_table = (
                self.page.locator("table").filter(has_text=endpoint_alias).locator("tbody").first
            )
        endpoints_table.wait_for(state="visible", timeout=20000)
        table_text = endpoints_table.inner_text()
        assert endpoint_alias in table_text, "Алиас эндпоинта отсутствует в таблице"
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

    def change_release_version(
        self,
        version_label: str = "Initial",
        *,
        avoid_commit_message: str | None = None,
    ):
        """
        Меняет версию релиза (привязку к другому коммиту).
        В UI список коммитов как при create_release; подписи вроде «Initial» часто отсутствуют —
        тогда надёжнее выбрать строку таблицы, отличную от коммита релиза (avoid_commit_message).
        """
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
        self.page.wait_for_timeout(500)
        version_field = self.page.get_by_role("textbox", name="version")
        version_field.wait_for(state="visible", timeout=10000)
        version_field.click()
        self.page.wait_for_timeout(500)

        try:
            self.page.locator("label").nth(2).click()
            self.page.wait_for_timeout(300)
        except Exception:
            pass
        commits_btn = self.page.locator("button").filter(has_text="Коммиты")
        if commits_btn.count() > 0:
            commits_btn.first.click()
            self.page.wait_for_timeout(500)

        # Модалка смены версии: та, где есть поле version (не «последний» dialog — он может быть другим)
        version_tb = self.page.get_by_role("textbox", name="version")
        dlg_with_version = self.page.get_by_role("dialog").filter(has=version_tb)
        dialog = dlg_with_version.first if dlg_with_version.count() > 0 else self.page.get_by_role("dialog").last

        # Таблица коммитов; клик по <tr> перехватывается вкладкой — кликаем td с force
        rows = dialog.locator("tbody tr")
        if rows.count() == 0:
            rows = self.page.locator("tbody tr")
        rows.first.wait_for(state="visible", timeout=15000)
        n = rows.count()

        def _click_row(idx: int) -> None:
            cell = rows.nth(idx).locator("td").first
            cell.click(force=True)
            self.page.wait_for_timeout(300)

        picked = False
        if avoid_commit_message and n >= 2:
            for i in range(n):
                txt = rows.nth(i).inner_text() or ""
                if avoid_commit_message not in txt:
                    _click_row(i)
                    picked = True
                    break
        if not picked:
            for exact in (True, False):
                try:
                    opt = dialog.get_by_text(version_label, exact=exact).first
                    opt.wait_for(state="visible", timeout=4000)
                    opt.click(force=True)
                    picked = True
                    break
                except Exception:
                    continue
        if not picked:
            for pattern in (r"Initial\s+commit", r"\bInitial\b"):
                try:
                    opt = dialog.get_by_text(re.compile(pattern, re.IGNORECASE)).first
                    opt.wait_for(state="visible", timeout=4000)
                    opt.click(force=True)
                    picked = True
                    break
                except Exception:
                    continue
        if not picked and n >= 1:
            _click_row(0)
            picked = True
        if not picked:
            raise RuntimeError(
                f"Не удалось выбрать коммит для смены версии (version_label={version_label!r}, строк={n})"
            )

        send_button = self.page.get_by_role("button", name="Отправить")
        send_button.wait_for(state="visible", timeout=10000)
        send_button.click(force=True)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def delete_release(self):
        """Удаляет релиз"""
        self.page.get_by_role("button", name="release_delete_button").click()
        self.page.get_by_role("button", name="Удалить").click()
        self.page.wait_for_timeout(2000)

    def goto_releases_link(self):
        """Переход в раздел релизов через ссылку в навигации"""
        self.page.get_by_role("link", name="Релизы").click()
        self.page.wait_for_load_state("networkidle")
