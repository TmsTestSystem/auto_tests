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

# Добавляем поддержку --host параметра
def pytest_addoption(parser):
    """Добавляем кастомные опции pytest"""
    parser.addoption(
        "--test-host", 
        action="store", 
        default=None,
        help="Выбор хоста для тестирования (st1, st2, st3, st4, local-a, local-b, local-c, local-192)"
    )

def pytest_configure(config):
    """Настройка pytest при запуске"""
    host = config.getoption("--test-host")
    if host:
        # Маппинг хостов на URL (как в run_tests.py)
        host_urls = {
            "st1": "https://decision-flow-web-1.df-st1.cloud.b-pl.pro",
            "st2": "https://decision-flow-web-1.df-st2.cloud2.b-pl.pro", 
            "st3": "https://decision-flow-frontend-st3.df-st.b-pl.cloud2",
            "st4": "https://decision-flow-web-1.df-st4.cloud2.b-pl.pro",
            "local-a": "http://localhost:3333",
            "local-b": "http://localhost:3334", 
            "local-c": "http://localhost:3335",
            "local-192": "http://192.168.0.7:3333"
        }
        
        if host in host_urls:
            base_url = host_urls[host]
            # Обновляем .env файл
            env_content = f"""# Конфигурация хостов для тестирования
# Автоматически обновлено для хоста: {host}

BASE_URL={base_url}
LOGIN=admin@balance-pl.ru
PASSWORD=admin

DATABASE_URL=$env.DATABASE_URL
REPO_URL_FLOW=git@gitlab.infra.b-pl.pro:ilya.kurilin/qa_auto_test.git
"""
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # Перезагружаем переменные окружения
            load_dotenv(dotenv_path=env_path, override=True)
            print(f"[HOST] Выбран хост: {host}")
            print(f"[URL] BASE_URL установлен: {base_url}")
        else:
            print(f"[WARNING] Неизвестный хост '{host}'. Доступные: {', '.join(host_urls.keys())}")

# Хост настраивается через run_tests.py скрипт или --host параметр

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

def wait_for_canvas_with_refresh(page, timeout=10000, max_refreshes=1):
    """
    Ждет загрузки canvas диаграммы с автоматическим рефрешем при таймауте.
    При запуске всех тестов разом канвас может залипать дольше обычного.
    
    Args:
        page: Playwright page объект
        timeout (int): Таймаут ожидания в миллисекундах
        max_refreshes (int): Максимальное количество рефрешей при таймауте
        
    Returns:
        bool: True если canvas загружен, False если не удалось загрузить даже после рефрешей
    """
    from pages.canvas_utils import CanvasUtils
    canvas_utils = CanvasUtils(page)
    return canvas_utils.wait_for_canvas_with_refresh(timeout=timeout, max_refreshes=max_refreshes)

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
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
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
        try:
            yield page, existing['code']
        finally:
            # Очистка после теста в любом случае
            try:
                delete_project_by_id(existing['id'])
                print(f"[SUCCESS] Проект {existing['code']} удален")
            except Exception as e:
                print(f"[WARNING] Ошибка при удалении проекта {existing['code']}: {e}")
    else:
            # Создаём новый проект
            git = "/opt/app/empty_repo"
            default_branch = "master"
            project_page.open_create_project_modal()
            project_page.create_project(project_title, project_code, git, default_branch)
            project_page.wait_modal_close()
            
            # Переходим в проект перед импортом
            project_page.goto_project(project_code)
            time.sleep(2)
            
            # Импортируем проект через API
            print("[INFO] Импортируем проект через API...")
            project_page.import_project()
            time.sleep(5)
            print("[SUCCESS] Проект импортирован через API")
            
            try:
                yield page, project_code
            finally:
                # Очистка после теста в любом случае
                try:
                    project_info = get_project_by_code(project_code)
                    if project_info and 'id' in project_info:
                        delete_project_by_id(project_info['id'])
                        print(f"[SUCCESS] Проект {project_code} удален")
                    else:
                        print(f"[WARNING] Не удалось получить информацию о проекте {project_code}")
                except Exception as e:
                    print(f"[WARNING] Ошибка при удалении проекта {project_code}: {e}")


def create_project_via_api(title: str, code: str, git_url: str = "/opt/app/empty_repo", default_branch: str = "master"):
    """Создать проект через API"""
    data = {
        "title": title,
        "code": code,
        "git_url": git_url,
        "default_branch": default_branch,
        "gradient": "blue",  # Добавляем обязательное поле
        "description": f"API тестовый проект {code}",  # Добавляем обязательное поле
        "git": git_url  # Добавляем обязательное поле
    }
    
    try:
        response = requests.post(get_projects_api(), json=data, cookies=get_auth_cookies(), verify=False, timeout=30)
        
        if response.status_code == 422:
            print(f"[DEBUG] Ошибка валидации при создании проекта:")
            print(f"[DEBUG] Данные: {data}")
            print(f"[DEBUG] Ответ сервера: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ошибка при создании проекта {code}: {e}")
        raise


def delete_project_via_api(project_id: str):
    """Удалить проект через API"""
    url = f"{get_projects_api()}/{project_id}"
    
    try:
        response = requests.delete(url, cookies=get_auth_cookies(), verify=False, timeout=30)
        response.raise_for_status()
        return response.status_code == 204
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ошибка при удалении проекта {project_id}: {e}")
        raise


@pytest.fixture(scope="session")
def api_project():
    """Фикстура для создания проекта через API"""
    import uuid
    
    # Создаем проект через API
    unique_id = str(uuid.uuid4())[:8]
    project_title = f"API Test Project {unique_id}"
    project_code = f"api_test_{unique_id}"
    
    print(f"[API_SETUP] Создаем проект через API: {project_code}")
    
    project_info = None
    try:
        project_info = create_project_via_api(project_title, project_code)
        print(f"[API_SETUP] Проект создан: {project_info}")
        
        yield project_code, project_info
        
    except Exception as e:
        print(f"[API_ERROR] Не удалось создать проект: {e}")
        # Fallback - используем существующий проект
        project_code = "regr"
        print(f"[API_FALLBACK] Используем существующий проект: {project_code}")
        yield project_code, None
    
    # Очистка - удаляем проект если он был создан
    if project_info:
        try:
            delete_project_via_api(project_info['id'])
            print(f"[API_CLEANUP] Проект {project_code} удален (ID: {project_info['id']})")
        except Exception as cleanup_error:
            print(f"[API_WARN] Ошибка при удалении проекта: {cleanup_error}")


@pytest.fixture(scope="session")
def file_panel_api(api_project):
    """Фикстура для создания API клиента файловой панели"""
    from api.file_panel_api import FilePanelAPI
    
    project_code, project_info = api_project
    
    print(f"[FILE_PANEL_SETUP] Используем проект: {project_code}")
    file_panel = FilePanelAPI(project_code)
    
    yield file_panel
    
    print(f"[FILE_PANEL_CLEANUP] Тест завершен для проекта: {project_code}")

