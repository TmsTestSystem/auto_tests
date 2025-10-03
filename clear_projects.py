import os
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

API_BASE_URL = os.getenv("BASE_URL", "http://localhost:3333").rstrip("/")
PROJECTS_API = f"{API_BASE_URL}/api/projects"

def get_auth_cookies():
    """
    Получить куки авторизации через API логин
    """
    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    resp = requests.post(f"{API_BASE_URL}/api/auth/sign_in", json={"email": email, "password": password})
    resp.raise_for_status()
    return resp.cookies

def get_all_projects():
    """
    Получить все проекты через API
    """
    cookies = get_auth_cookies()
    resp = requests.get(PROJECTS_API, cookies=cookies)
    resp.raise_for_status()
    return resp.json()

def delete_project_by_id(project_id):
    """
    Удалить проект по ID через API
    """
    cookies = get_auth_cookies()
    resp = requests.delete(f"{PROJECTS_API}/{project_id}", cookies=cookies)
    resp.raise_for_status()
    return resp.status_code == 204

def clear_autotest_projects():
    """
    Удаляет все проекты, созданные автотестами
    """
    try:
        print("[INFO] Получаем список всех проектов...")
        projects = get_all_projects()
        print(f"[INFO] Найдено {len(projects)} проектов")
        
        autotest_projects = []
        
        # Ищем проекты, созданные автотестами
        for project in projects:
            project_code = project.get("code", "")
            project_title = project.get("title", "")
            
            # Проверяем паттерны автотестовых проектов
            is_autotest = (
                project_code.startswith("autotest_flow_") or
                project_code.startswith("test_flow_component_") or
                project_title.startswith("Автотест Flow") or
                project_title.startswith("Test Flow Project") or
                "autotest" in project_code.lower() or
                "test_flow" in project_code.lower()
            )
            
            if is_autotest:
                autotest_projects.append(project)
        
        if not autotest_projects:
            print("[INFO] Проекты автотестов не найдены")
            return
        
        print(f"[INFO] Найдено {len(autotest_projects)} проектов автотестов:")
        for project in autotest_projects:
            print(f"  - {project.get('code')} ({project.get('title')})")
        
        # Удаляем проекты
        deleted_count = 0
        for project in autotest_projects:
            try:
                project_id = project.get("id")
                project_code = project.get("code")
                project_title = project.get("title")
                
                print(f"[INFO] Пытаемся удалить проект: {project_code} (ID: {project_id})")
                
                if project_id:
                    try:
                        success = delete_project_by_id(project_id)
                        if success:
                            print(f"[SUCCESS] Удален проект: {project_code}")
                            deleted_count += 1
                        else:
                            print(f"[ERROR] API вернул ошибку при удалении проекта: {project_code}")
                    except requests.exceptions.HTTPError as e:
                        print(f"[ERROR] HTTP ошибка при удалении проекта {project_code}: {e}")
                        print(f"[DEBUG] Status code: {e.response.status_code}")
                        print(f"[DEBUG] Response text: {e.response.text}")
                        if e.response.status_code == 404:
                            print(f"[INFO] Проект {project_code} уже удален (404)")
                            deleted_count += 1
                    except Exception as e:
                        print(f"[ERROR] Ошибка при удалении проекта {project_code}: {e}")
                else:
                    print(f"[ERROR] У проекта {project_code} отсутствует ID")
            except Exception as e:
                print(f"[ERROR] Общая ошибка при обработке проекта {project.get('code')}: {e}")
        
        print(f"[INFO] Успешно удалено {deleted_count} из {len(autotest_projects)} проектов автотестов")
        
    except Exception as e:
        print(f"[ERROR] Ошибка при получении списка проектов: {e}")

def clear_shared_project_file():
    """
    Удаляет файл с кодом общего проекта
    """
    shared_project_file = "shared_project_code.txt"
    if os.path.exists(shared_project_file):
        try:
            os.remove(shared_project_file)
            print(f"[INFO] Удален файл: {shared_project_file}")
        except Exception as e:
            print(f"[ERROR] Ошибка при удалении файла {shared_project_file}: {e}")
    else:
        print(f"[INFO] Файл {shared_project_file} не найден")

def create_test_project():
    """
    Создает тестовый проект для демонстрации функции очистки
    """
    try:
        from pages.project_page import ProjectPage
        from playwright.sync_api import sync_playwright
        from pages.login_page import LoginPage
        
        print("[INFO] Создаем тестовый проект для демонстрации...")
        
        email = os.getenv("LOGIN")
        password = os.getenv("PASSWORD")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            login_page = LoginPage(page)
            login_page.goto()
            login_page.login(email, password)
            
            project_page = ProjectPage(page)
            unique = int(time.time())
            project_code = f"autotest_demo_{unique}"
            project_title = f"Autotest Demo {unique}"
            repo_url = "git@gitlab.infra.b-pl.pro:ilya.kurilin/qa_auto_test.git"
            
            project_page.open_create_project_modal()
            project_page.create_project(project_title, project_code, repo_url, "main")
            
            # Упрощенное ожидание - просто ждем немного
            time.sleep(3)
            
            browser.close()
            print(f"[SUCCESS] Создан тестовый проект: {project_code}")
            
    except Exception as e:
        print(f"[ERROR] Ошибка при создании тестового проекта: {str(e)}")

if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("ОЧИСТКА ПРОЕКТОВ АВТОТЕСТОВ")
    print("=" * 60)
    
    # Если передан аргумент --demo, создаем тестовый проект
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        create_test_project()
        print()
    
    clear_autotest_projects()
    print()
    clear_shared_project_file()
    
    print("=" * 60)
    print("ОЧИСТКА ЗАВЕРШЕНА")
    print("=" * 60)
