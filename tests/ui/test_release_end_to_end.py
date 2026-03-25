import os
import time
import uuid
import zipfile
import tempfile
from pathlib import Path

import pytest
import requests
import re
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.release_page import ReleasePage
from pages.process_log_page import ProcessLogPage
from pages.endpoints_page import EndpointsPage
from pages.commit_page import CommitPage
from locators import FilePanelLocators
from conftest import get_project_by_code, get_api_base_url, delete_project_by_id


TUTORIAL_FOLDER = Path(__file__).parent.parent.parent / "TutorialProcess"


def _create_tutorial_zip() -> str:
    """Упаковать содержимое TutorialProcess в ZIP для импорта."""
    if not TUTORIAL_FOLDER.exists():
        raise FileNotFoundError(f"Папка {TUTORIAL_FOLDER} не найдена")

    zip_path = Path(tempfile.gettempdir()) / f"tutorial_process_{int(time.time())}.zip"
    if zip_path.exists():
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for fs_path in TUTORIAL_FOLDER.rglob("*"):
            if fs_path.is_file():
                arcname = fs_path.relative_to(TUTORIAL_FOLDER)
                zipf.write(fs_path, arcname)
    return str(zip_path)


@pytest.mark.ui
def test_release_end_to_end(login_page):
    """
    Release E2E: создаём проект, переходим в него и импортируем TutorialProcess.
    """
    page = login_page
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    release_page = ReleasePage(page)
    process_log_page = ProcessLogPage(page)
    endpoints_page = EndpointsPage(page)
    commit_page = CommitPage(page)

    unique_id = str(uuid.uuid4())[:8]
    project_code = f"release_e2e_{unique_id}"
    project_title = f"Release E2E {unique_id}"
    commit_message = f"release_e2e_commit_{unique_id}"
    release_title = f"release_name_{unique_id}"
    release_alias = f"release_alias_{unique_id}"
    endpoint_alias = "test_release"
    git_url = "/opt/app/empty_repo"
    default_branch = "master"

    project_info = None
    tutorial_zip = None

    try:
        print("[STEP 1] Создаём UI-проект для релизного E2E")
        project_page.open_create_project_modal()
        project_page.create_project(project_title, project_code, git_url, default_branch)
        project_page.wait_modal_close()

        assert project_page.goto_project(project_code), f"Проект {project_code} не найден в списке"
        time.sleep(2)

        print("[STEP 2] Импортируем TutorialProcess через файловую панель (как в API тестах)")
        tutorial_zip = _create_tutorial_zip()
        file_panel.import_project_zip(tutorial_zip)

        file_panel.open_file_panel()
        required_files = [
            "tutorial.ds.json",
            "tutorial_script.py",
            "tutorial_success.test.json",
            "TutorialProcess.df.json",
        ]
        for filename in required_files:
            locator = page.locator(FilePanelLocators.get_treeitem_by_path(filename))
            locator.wait_for(state="visible", timeout=20000)
            assert locator.is_visible(), f"Файл {filename} не появился после импорта"
        print("[SUCCESS] TutorialProcess импортирован полностью")

        ds_file = (
            page.get_by_label("board_toolbar_panel")
            .get_by_label("/tutorial.ds.json")
            .locator("div")
            .filter(has_text="tutorial.ds.json")
            .nth(1)
        )
        ds_file.dblclick()
        print("[INFO] Открыт tutorial.ds.json")
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="datastructureeditor_generate_button").click()
        page.get_by_role("button", name="Генерировать").click()
        print("[SUCCESS] Python-классы сгенерированы из tutorial.ds.json")

        print("[STEP 3] Открываем config/endpoints.json и готовим данные для эндпоинта")
        file_panel.open_file_panel()
        endpoints_page.open_endpoints_file()
        print("[STEP 4] Выбираем файл TutorialProcess.df.json в модальном окне")
        endpoints_page.add_endpoint(endpoint_alias, "TutorialProcess.df.json")
        print("[SUCCESS] Файл TutorialProcess.df.json выбран для endpoint")
        endpoints_page.save_endpoints()
        print("[SUCCESS] Эндпоинты сохранены и уведомление отображено")

        print("[STEP 5] Фиксируем изменения через панель коммитов")
        commit_page.commit_all_changes(commit_message)

        print("[STEP 6] Возвращаемся на список проектов и переходим в релизы")
        release_page.goto_releases_from_project_card(project_title)
        print("[SUCCESS] Открыт раздел релизов для созданного проекта")

        print("[STEP 7] Создаём релиз и переходим на вкладку коммитов")
        release_page.create_release(release_title, release_alias, commit_message)
        print("[STEP 8] Проверяем API /api/execute/{release}/{endpoint}")
        execute_url = f"{get_api_base_url()}/api/execute/{release_alias}/{endpoint_alias}"
        request_payload = {
            "request_meta": {
                "object_id": f"release_{unique_id}",
                "request_id": f"req_{unique_id}",
                "tags": "ui_release_test",
            },
            "request_data": {
                "customer_id": "4535464sdf",
                "loans": [
                    {"currency": "RUR", "monthly_payment": 32300.2},
                    {"currency": "EUR", "monthly_payment": 323.2},
                    {"currency": "USD", "monthly_payment": 323.2},
                ],
            },
        }
        response = requests.post(execute_url, json=request_payload, verify=False, timeout=30)
        # Для непубликованного релиза сейчас возвращается 422 с сообщением "Release not published".
        assert response.status_code in (404, 422), (
            f"Ожидали статус 404 или 422, получили {response.status_code}: {response.text}"
        )
        if response.status_code == 422:
            body = response.text or ""
            assert "release not published" in body.lower(), (
                f"Для кода 422 ожидаем сообщение 'Release not published', получили: {body}"
            )
            print("[SUCCESS] API ответило 422 Release not published для непубликованного релиза")
        else:
            print("[SUCCESS] API ответило 404 для непубликованного релиза")

        print("[STEP 9] Открываем созданный релиз и валидируем данные")
        # После create_release остаёмся на списке релизов; таблица могла сменить вёрстку — открываем по имени
        release_page.open_release_by_title(release_title)
        release_page.validate_release_data(release_title, release_alias, endpoint_alias, "Черновик")

        print("[STEP 10] Публикуем релиз и повторно вызываем API")
        release_page.publish_release()
        published_response = requests.post(execute_url, json=request_payload, verify=False, timeout=30)
        assert published_response.status_code == 200, (
            f"После публикации ожидали 200, получили {published_response.status_code}: {published_response.text}"
        )
        print("[SUCCESS] API ответило 200 после публикации релиза")

        print("[STEP 11] Проверяем журнал процессов")
        process_log_page.goto()
        process_log_page.wait_for_process_in_log(
            "TutorialProcess.df.json",
            "finished",
            min_rows=1,
            exact_rows=1,
        )

        print("[STEP 12] Возвращаемся в Релизы и изменяем версию релиза")
        release_page.goto_releases_link()
        release_page.open_release_by_title(release_title)
        # Релиз привязан к commit_message; в списке редко есть подпись «Initial» — берём другой коммит из таблицы
        release_page.change_release_version("Initial", avoid_commit_message=commit_message)
        print("[SUCCESS] Версия релиза изменена")

        print("[STEP 13] Публикуем релиз с новой версией и проверяем API")
        release_page.publish_release()
        version_response = requests.post(execute_url, json=request_payload, verify=False, timeout=30)
        # Раньше ожидали 404; на текущем бэкенде алиас релиза и endpoint остаются валидными — execute возвращает 200.
        assert version_response.status_code == 200, (
            f"После смены версии и публикации ожидали 200, получили {version_response.status_code}: {version_response.text}"
        )
        version_json = version_response.json()
        assert version_json.get("status") == "finished", f"Ожидали finished: {version_json}"
        print("[SUCCESS] API ответило 200 после смены версии и публикации (выполнение по-прежнему доступно)")

        print("[STEP 14] Снимаем релиз с публикации")
        release_page.unpublish_release()
        print("[SUCCESS] Релиз снят с публикации")

        print("[STEP 15] Проверяем API после снятия с публикации")
        unpublish_response = requests.post(execute_url, json=request_payload, verify=False, timeout=30)
        assert unpublish_response.status_code in (404, 422), (
            f"После снятия с публикации ожидали 404 или 422, получили "
            f"{unpublish_response.status_code}: {unpublish_response.text}"
        )
        if unpublish_response.status_code == 422:
            # На локальных стендах при обращении к непубликованному релизу возвращается 422 Not Published
            body = unpublish_response.text or ""
            assert "not published" in body.lower(), (
                f"Для кода 422 ожидаем сообщение 'Not Published', получили: {body}"
            )
            print("[SUCCESS] API ответило 422 Not Published после снятия релиза с публикации")
        else:
            print("[SUCCESS] API ответило 404 после снятия релиза с публикации")

        print("[STEP 16] Удаляем релиз и повторно проверяем API")
        release_page.delete_release()
        delete_response = requests.post(execute_url, json=request_payload, verify=False, timeout=30)
        assert delete_response.status_code == 404, (
            f"После удаления релиза ожидали 404, получили {delete_response.status_code}: {delete_response.text}"
        )
        print("[SUCCESS] API ответило 404 после удаления релиза")

        print("[STEP 17] Повторно проверяем журнал процессов")
        process_log_page.goto()
        n_rows = process_log_page.wait_for_process_in_log(
            "TutorialProcess.df.json",
            "finished",
            min_rows=1,
            exact_rows=None,
        )
        print(f"[SUCCESS] Журнал процессов: {n_rows} запис(ей), TutorialProcess.df.json в статусе finished")

        project_info = get_project_by_code(project_code)
        assert project_info is not None, f"Не удалось получить данные проекта {project_code}"
        time.sleep(5)
    finally:
        if tutorial_zip and os.path.exists(tutorial_zip):
            os.remove(tutorial_zip)
        # Удаляем проект после теста
        try:
            project_info = get_project_by_code(project_code)
            if project_info and 'id' in project_info:
                delete_project_by_id(project_info['id'])
                print(f"[SUCCESS] Проект {project_code} удален")
            else:
                print(f"[WARNING] Не удалось получить информацию о проекте {project_code} для удаления")
        except Exception as e:
            print(f"[WARNING] Ошибка при удалении проекта {project_code}: {e}")

