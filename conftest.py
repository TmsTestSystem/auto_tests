import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from dotenv import load_dotenv
import os
import time
from pathlib import Path
import requests
import uuid
import urllib3

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Хост настраивается через run_tests.py скрипт

def get_api_base_url():
    """Получить BASE_URL из переменных окружения"""
    return os.getenv("BASE_URL", "http://localhost:3333").rstrip("/")

def get_projects_api():
    """Получить URL для API проектов"""
    return f"{get_api_base_url()}/api/projects"


def get_auth_cookies():
    """
    Получить куки авторизации через API логин
    """
    import requests
    import urllib3
    # Отключаем предупреждения о небезопасных запросах
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    api_base_url = get_api_base_url()
    resp = requests.post(f"{api_base_url}/api/auth/sign_in", json={"email": email, "password": password}, verify=False)
    resp.raise_for_status()
    return resp.cookies

def get_project_by_code(code):
    cookies = get_auth_cookies()
    projects_api = get_projects_api()
    resp = requests.get(projects_api, cookies=cookies, verify=False)
    resp.raise_for_status()
    for prj in resp.json():
        if prj.get("code") == code:
            return prj
    return None

def delete_project_by_id(project_id):
    cookies = get_auth_cookies()
    projects_api = get_projects_api()
    resp = requests.delete(f"{projects_api}/{project_id}", cookies=cookies, verify=False)
    resp.raise_for_status()
    return resp.status_code == 204

def save_screenshot(page, test_name):
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    screenshot_base = test_name
    screenshot_path = os.path.join(screenshots_dir, f"{screenshot_base}.png")
    # Если файл уже есть, добавляем timestamp
    if os.path.exists(screenshot_path):
        screenshot_path = os.path.join(screenshots_dir, f"{screenshot_base}_{int(time.time())}.png")
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"[SCREENSHOT] Скриншот сохранён: {screenshot_path}")

def get_all_projects_via_api():
    cookies = get_auth_cookies()
    projects_api = get_projects_api()
    resp = requests.get(projects_api, cookies=cookies, verify=False)
    resp.raise_for_status()
    return resp.json()

@pytest.fixture(scope="function")
def login_page():
    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    assert email is not None, "LOGIN not set"
    assert password is not None, "PASSWORD not set"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_page = LoginPage(page)
        login_page.goto()
        login_page.login(email, password)
        yield page
        browser.close()

@pytest.fixture(scope="function")
def flow_project(login_page):
    """
    Фикстура для создания проекта с git-репозиторием из REPO_URL_FLOW
    Если проект с нужным кодом уже есть — не создавать, а использовать существующий.
    """
    from pages.project_page import ProjectPage
    import os
    import time
    import uuid
    page = login_page
    project_page = ProjectPage(page)

    # Если задан EXISTING_PROJECT_CODE, используем его и не создаём новые проекты
    existing_code = os.getenv("EXISTING_PROJECT_CODE")
    if existing_code:
        yield page, existing_code
        return

    # Генерируем уникальный код проекта
    unique_id = str(uuid.uuid4())[:8]
    project_code = f"test_flow_component_{unique_id}"
    project_title = f"Test Flow Project {unique_id}"

    # Проверяем, есть ли уже проект с нужным кодом (начинается с test_flow_component_)
    all_projects = get_all_projects_via_api()
    existing = None
    for prj in all_projects:
        if prj['code'].startswith('test_flow_component_'):
            existing = prj
            break

    if existing:
        # Если проект уже есть, используем его
        yield page, existing['code']
    else:
        # Создаём новый проект
        git = os.environ.get("REPO_URL_FLOW")
        default_branch = "main"
        project_page.open_create_project_modal()
        project_page.create_project(project_title, project_code, git, default_branch)
        project_page.wait_modal_close()
        yield page, project_code


# Файл для хранения project_code между тестами
SHARED_PROJECT_FILE = "shared_project_code.txt"

def get_or_create_shared_project(login_page):
    """
    Функция для получения или создания общего проекта между тестами flow.
    Если тесты запускаются последовательно - используется один проект.
    Если тест запускается отдельно - создается новый проект.
    """
    # Проверяем, есть ли сохраненный код проекта
    shared_project_code = None
    if os.path.exists(SHARED_PROJECT_FILE):
        try:
            with open(SHARED_PROJECT_FILE, 'r') as f:
                shared_project_code = f.read().strip()
        except Exception:
            pass
    
    # Если есть код проекта - проверяем, существует ли проект
    if shared_project_code:
        existing_project = get_project_by_code(shared_project_code)
        if existing_project:
            return shared_project_code
        else:
            # Проект был удален, удаляем файл
            try:
                os.remove(SHARED_PROJECT_FILE)
            except Exception:
                pass
    
    # Создаем новый проект
    unique = int(time.time())
    project_code = f"autotest_flow_shared_{unique}"
    project_title = f"Автотест Flow Shared {unique}"
    repo_url = "git@gitlab.infra.b-pl.pro:ilya.kurilin/qa_auto_test.git"
    
    # Создаем проект через UI
    from pages.project_page import ProjectPage
    project_page = ProjectPage(login_page)
    project_page.open_create_project_modal()
    project_page.create_project(project_title, project_code, repo_url, "main")
    project_page.wait_modal_close()
    
    # Сохраняем код проекта в файл для следующих тестов
    try:
        with open(SHARED_PROJECT_FILE, 'w') as f:
            f.write(project_code)
    except Exception:
        pass
    
    return project_code

@pytest.fixture(scope="function")
def shared_flow_project(login_page):
    """
    Фикстура для общего проекта между тестами flow.
    """
    return get_or_create_shared_project(login_page)

@pytest.fixture(scope="session", autouse=True)
def cleanup_shared_project():
    """
    Автоматически удаляет общий проект в конце сессии тестов
    """
    yield  # Выполняем все тесты
    
    # После выполнения всех тестов удаляем проект и файл
    if os.path.exists(SHARED_PROJECT_FILE):
        try:
            with open(SHARED_PROJECT_FILE, 'r') as f:
                project_code = f.read().strip()
            
            prj = get_project_by_code(project_code)
            if prj and prj.get("id"):
                delete_project_by_id(prj["id"])
                print(f"[CLEANUP] Удален общий проект: {project_code}")
            
            # Удаляем файл
            os.remove(SHARED_PROJECT_FILE)
        except Exception as e:
            print(f"[CLEANUP] Ошибка при удалении проекта: {e}")
            # Все равно пытаемся удалить файл
            try:
                os.remove(SHARED_PROJECT_FILE)
            except Exception:
                pass 