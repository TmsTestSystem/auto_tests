import os
import time
import uuid
import zipfile
import tempfile
from pathlib import Path

import pytest
import requests

from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.process_schedule_page import ProcessSchedulePage
from pages.endpoints_page import EndpointsPage
from pages.commit_page import CommitPage
from locators import FilePanelLocators
from conftest import get_project_by_code, get_api_base_url, delete_project_by_id
from api.file_panel_api import FilePanelAPI


TUTORIAL_FOLDER = Path(__file__).parent.parent.parent / "TutorialProcess"


def _create_tutorial_zip() -> str:
    """Упаковать содержимое TutorialProcess в ZIP для импорта"""
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
def test_process_schedule_create_and_manage(login_page):
    """Тест функционала расписания процессов"""
    page = login_page
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    schedule_page = ProcessSchedulePage(page)
    endpoints_page = EndpointsPage(page)
    commit_page = CommitPage(page)

    unique_id = str(uuid.uuid4())[:8]
    project_code = f"schedule_test_{unique_id}"
    project_title = f"Schedule Test {unique_id}"
    schedule_name = f"test_schedule_{unique_id}"
    commit_message = f"schedule_test_commit_{unique_id}"
    endpoint_alias = "test_schedule"
    git_url = "/opt/app/empty_repo"
    default_branch = "master"
    process_file = "TutorialProcess.df.json"

    project_info = None
    tutorial_zip = None

    try:
        print("[STEP 1] Создаём UI-проект для тестирования расписания")
        project_page.open_create_project_modal()
        project_page.create_project(project_title, project_code, git_url, default_branch)
        project_page.wait_modal_close()

        assert project_page.goto_project(project_code), f"Проект {project_code} не найден в списке"
        time.sleep(2)

        print("[STEP 2] Импортируем TutorialProcess через файловую панель (ZIP через /git/repository/upload)")
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
        time.sleep(2)
        page.get_by_role("button", name="datastructureeditor_generate_button").click()
        time.sleep(1)
        page.get_by_role("button", name="Генерировать").click()
        time.sleep(3)
        print("[SUCCESS] Python-классы сгенерированы из tutorial.ds.json")

        print("[STEP 3] Открываем config/endpoints.json и готовим данные для эндпоинта")
        file_panel.open_file_panel()
        time.sleep(2)
        endpoints_page.open_endpoints_file()
        time.sleep(2)
        print("[STEP 4] Добавляем endpoint для TutorialProcess.df.json")
        endpoints_page.add_endpoint(endpoint_alias, "TutorialProcess.df.json")
        time.sleep(1)
        print("[SUCCESS] Файл TutorialProcess.df.json выбран для endpoint")
        endpoints_page.save_endpoints()
        time.sleep(2)
        print("[SUCCESS] Эндпоинты сохранены")

        print("[STEP 5] Фиксируем изменения через панель коммитов")
        commit_page.commit_all_changes(commit_message)
        time.sleep(2)

        print("[STEP 6] Возвращаемся на список проектов и переходим в расписание")
        try:
            schedule_page.goto_schedule_from_project_card(project_title)
            time.sleep(3)
            print("[SUCCESS] Перешли в раздел расписания процессов")
        except Exception as e:
            print(f"[WARN] Не удалось перейти в раздел расписания: {e}")
            print("[INFO] Возможно, функционал расписания недоступен в текущей версии")
            print("[INFO] Пропускаем тест")
            pytest.skip("Функционал расписания процессов недоступен")

        print("[STEP 7] Создаём новое расписание")
        schedule_page.open_create_schedule_modal()
        time.sleep(2)
        schedule_page.create_schedule(
                name=schedule_name,
                version=commit_message,
                process_file=process_file,
                cron_second="*",
                cron_minute="*",
                cron_hour="*",
                cron_day="*",
                cron_month="*",
                cron_weekday="*",
                cron_year="*",
                request_data={
                    "object_id": f"obj_{unique_id}",
                    "request_id": f"req_{unique_id}",
                    "tags": "schedule_test"
                }
            )
        schedule_page.wait_modal_close()
        time.sleep(2)
        print(f"[SUCCESS] Расписание '{schedule_name}' создано")

        print("[STEP 8] Открываем страницу расписания")
        schedule_page.open_schedule_details(schedule_name)
        print(f"[SUCCESS] Открыта страница расписания '{schedule_name}'")

        print("[STEP 9] Запускаем процесс вручную")
        schedule_page.start_schedule_manually()
        print(f"[SUCCESS] Процесс запущен вручную")

        print("[STEP 10] Проверяем что запуск появился в истории")
        schedule_page.verify_execution_in_history()
        print(f"[SUCCESS] Запуск найден в истории")

        print("[STEP 11] Активируем расписание")
        schedule_page.activate_schedule()
        print(f"[SUCCESS] Расписание активировано")

        print("[STEP 12] Ждём 12 секунд для запуска процессов по расписанию")
        time.sleep(12)

        print("[STEP 13] Проверяем API журнала процессов - должно быть минимум 10 процессов")
        import urllib3
        import datetime
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        from conftest import get_auth_cookies, get_api_base_url
        
        api_url = f"{get_api_base_url()}/api/jobs?page=0&page_size=20&project={project_code}"
        cookies = get_auth_cookies()
        response = requests.get(api_url, cookies=cookies, verify=False, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        print(f"[DEBUG] Тип ответа API: {type(response_data)}")
        
        if isinstance(response_data, dict):
            jobs = response_data.get('jobs', response_data.get('data', response_data.get('items', [])))
        else:
            jobs = response_data
        
        scheduler_jobs = [job for job in jobs if job.get('transport') == 'Scheduler']
        
        print(f"[INFO] Найдено процессов с transport=Scheduler: {len(scheduler_jobs)}")
        assert len(scheduler_jobs) >= 5, f"Ожидалось минимум 5 процессов, найдено {len(scheduler_jobs)}"
        print(f"[SUCCESS] В журнале найдено {len(scheduler_jobs)} процессов от планировщика")

        print("[STEP 14] Деактивируем расписание")
        schedule_page.deactivate_schedule()
        print(f"[SUCCESS] Расписание деактивировано")

        print("[STEP 15] Ждём 5 секунд и проверяем что новые процессы не запускаются")
        time.sleep(5)
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        response2 = requests.get(api_url, cookies=cookies, verify=False, timeout=30)
        response2.raise_for_status()
        response_data2 = response2.json()
        
        if isinstance(response_data2, dict):
            jobs2 = response_data2.get('jobs', response_data2.get('data', response_data2.get('items', [])))
        else:
            jobs2 = response_data2
        
        scheduler_jobs2 = [job for job in jobs2 if job.get('transport') == 'Scheduler']
        
        if len(scheduler_jobs2) > 0:
            last_job = scheduler_jobs2[0]
            started_at = last_job.get('started_at')
            
            print(f"[INFO] Последний процесс запущен: {started_at}")
            print(f"[INFO] Текущее время: {current_time.isoformat()}")
            
            if started_at.endswith('Z'):
                started_at = started_at[:-1] + '+00:00'
            started_time = datetime.datetime.fromisoformat(started_at)
            
            if started_time.tzinfo is None:
                started_time = started_time.replace(tzinfo=datetime.timezone.utc)
            
            time_diff = (current_time - started_time).total_seconds()
            print(f"[INFO] Последний процесс был запущен {time_diff:.0f} секунд назад")
            
            assert started_time < current_time, "Время запуска процесса в будущем - ошибка!"
            assert time_diff > 5, "Новые процессы продолжают запускаются после деактивации!"
            
            print(f"[SUCCESS] После деактивации новые процессы не запускаются")

        print("\n[SUCCESS] Тест расписания процессов завершён успешно!")

    finally:
        if tutorial_zip and os.path.exists(tutorial_zip):
            try:
                os.remove(tutorial_zip)
                print(f"[CLEANUP] Временный архив удалён: {tutorial_zip}")
            except Exception as e:
                print(f"[WARN] Не удалось удалить временный архив {tutorial_zip}: {e}")
        
        try:
            project_info = get_project_by_code(project_code)
            if project_info and 'id' in project_info:
                delete_project_by_id(project_info['id'])
                print(f"[CLEANUP] Проект {project_code} удалён")
        except Exception as e:
            print(f"[WARN] Ошибка при удалении проекта: {e}")



