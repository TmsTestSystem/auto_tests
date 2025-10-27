import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
import requests
import urllib3
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))
from conftest import get_auth_cookies, get_api_base_url
from custom_logger import setup_test_logger

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Отключаем предупреждения о небезопасных запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_api_projects_accessible():
    """Базовый тест доступности API проектов"""
    base_url = os.getenv("BASE_URL")
    assert base_url is not None, "BASE_URL not set"
    cookies = get_auth_cookies()
    # Проверяем доступ к списку проектов как к стабильно доступному эндпоинту
    resp = requests.get(f"{base_url.rstrip('/')}/api/projects", cookies=cookies, verify=False)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}, body: {resp.text}"
    assert isinstance(resp.json(), list)


def test_proj_func():
    """Полный цикл работы с проектом: создание, открытие, изменение, fetch, удаление"""
    logger = setup_test_logger("api_project_test")
    
    try:
        base_url = get_api_base_url()
        cookies = get_auth_cookies()
        
        # Генерируем уникальный код проекта
        unique_id = str(uuid.uuid4())[:8]
        project_title = f"API Test Project {unique_id}"
        project_code = f"api_test_{unique_id}"
        
        logger.info(f"[TEST] Полный цикл проекта: {project_code}")
        
        logger.info(f"[STEP 1] Создание проекта: {project_code}")
        create_data = {
            "title": project_title,
            "code": project_code,
            "git_url": "/opt/app/empty_repo",
            "default_branch": "master",
            "gradient": "blue",
            "description": f"API тестовый проект {project_code}",
            "git": "/opt/app/empty_repo"
        }
        
        create_resp = requests.post(f"{base_url}/api/projects", json=create_data, cookies=cookies, verify=False, timeout=30)
        assert create_resp.status_code == 200, f"Ошибка создания проекта: {create_resp.status_code}, {create_resp.text}"
        project_info = create_resp.json()
        project_id = project_info['id']
        logger.info(f"[SUCCESS] Проект создан: ID={project_id}, Code={project_code}")
        
        logger.info(f"[STEP 2] Открытие проекта (ensure_exist)")
        ensure_resp = requests.get(f"{base_url}/api/ide/{project_code}/branch/master/git/repository/ensure_exist", 
                                 cookies=cookies, verify=False, timeout=30)
        assert ensure_resp.status_code == 200, f"Ошибка ensure_exist: {ensure_resp.status_code}, {ensure_resp.text}"
        logger.info(f"[SUCCESS] Проект открыт и репозиторий инициализирован")
        
        logger.info(f"[STEP 3] Проверка доступности проекта")
        access_resp = requests.get(f"{base_url}/api/projects?project_code={project_code}", 
                                 cookies=cookies, verify=False, timeout=30)
        assert access_resp.status_code == 200, f"Ошибка проверки доступности: {access_resp.status_code}, {access_resp.text}"
        projects = access_resp.json()
        assert len(projects) > 0, "Проект не найден в списке"
        logger.info(f"[SUCCESS] Проект доступен в списке проектов")
        
        logger.info(f"[STEP 4] Изменение проекта")
        updated_title = f"{project_title}_UPDATED"
        update_data = {
            "title": updated_title,
            "code": project_code,
            "description": f"API тестовый проект {project_code} - ОБНОВЛЕН",
            "git": "/opt/app/empty_repo",
            "default_branch": "master",
            "gradient": "blue"
        }
        
        update_resp = requests.put(f"{base_url}/api/projects/{project_id}", 
                                 json=update_data, cookies=cookies, verify=False, timeout=30)
        assert update_resp.status_code == 200, f"Ошибка обновления проекта: {update_resp.status_code}, {update_resp.text}"
        logger.info(f"[SUCCESS] Проект обновлен: {updated_title}")
        
        logger.info(f"[STEP 5] Fetch проекта")
        fetch_resp = requests.post(f"{base_url}/api/ide/{project_code}/git/branches/fetch?prune=true", 
                                 cookies=cookies, verify=False, timeout=30)
        assert fetch_resp.status_code == 200, f"Ошибка fetch: {fetch_resp.status_code}, {fetch_resp.text}"
        logger.info(f"[SUCCESS] Fetch выполнен успешно")
        
        logger.info(f"[STEP 6] Удаление проекта")
        delete_resp = requests.delete(f"{base_url}/api/projects/{project_id}", 
                                    cookies=cookies, verify=False, timeout=30)
        assert delete_resp.status_code in [200, 204], f"Ошибка удаления проекта: {delete_resp.status_code}, {delete_resp.text}"
        logger.info(f"[SUCCESS] Проект удален: {project_code}")
        
        logger.info(f"[COMPLETE] Полный цикл проекта {project_code} выполнен успешно!")
        
    except Exception as e:
        logger.error(f"[ERROR] Ошибка в полном цикле проекта: {e}")
        try:
            if 'project_id' in locals():
                requests.delete(f"{base_url}/api/projects/{project_id}", cookies=cookies, verify=False, timeout=30)
                logger.info(f"[CLEANUP] Проект {project_code} удален при очистке")
        except Exception as cleanup_error:
            logger.warning(f"[WARN] Ошибка при очистке проекта: {cleanup_error}")
        raise
    finally:
        logger.close()