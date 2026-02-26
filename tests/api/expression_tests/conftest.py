import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import os
import uuid
import time
import json
import pytest
import requests
from utils.auth_utils import get_auth_cookies, get_api_base_url
from utils.custom_logger import setup_test_logger
from utils.project_zip_utils import create_project_zip, cleanup_temp_zip

@pytest.fixture(scope="session")
def expression_project():
    logger = setup_test_logger("expression_import_test")
    try:
        base_url = get_api_base_url()
        cookies = get_auth_cookies()
        unique_id = str(uuid.uuid4())[:8]
        project_title = f"Expression Project {unique_id}"
        project_code = f"expression_{unique_id}"
        logger.info(f"[EXP_SETUP] Создаём проект: {project_code}")
        create_data = {
            "title": project_title,
            "code": project_code,
            "description": f"Проект для expression API-тестов ({project_code})",
            "gradient": "#9D80CB,#F7C2E6",
            "type": "directory",
        }
        files = {
            "project_json": (None, json.dumps(create_data), "application/json"),
            "zip_template": ("empty.zip", b"", "application/octet-stream"),
        }
        response = requests.post(
            f"{base_url}/api/projects",
            cookies=cookies,
            files=files,
            verify=False,
            timeout=30,
        )
        response.raise_for_status()
        project_info = response.json()

        project_root = Path(__file__).parent.parent.parent.parent
        source_folder = project_root / "Project_expression"
        temp_zip_path = create_project_zip(str(source_folder))
        logger.info(f"[EXP_SETUP] ZIP создан: {temp_zip_path}")

        try:
            upload_url = f"{base_url}/api/ide/{project_code}/branch/master/git/repository/upload"
            with open(temp_zip_path, 'rb') as f:
                data = f.read()
            headers = {
                'Accept': '*/*',
                'Content-Type': 'application/binary',
            }
            upload_resp = requests.post(upload_url, data=data, headers=headers, cookies=cookies, verify=False, timeout=120)
            upload_resp.raise_for_status()
            logger.info(f"[EXP_SETUP] ZIP импортирован, статус: {upload_resp.status_code}")

            time.sleep(3)
        finally:
            cleanup_temp_zip(temp_zip_path)

        yield project_code, project_info
    finally:
        try:
            requests.delete(f"{base_url}/api/projects/{project_info['id']}", cookies=cookies, verify=False, timeout=30)
            logger.info(f"[EXP_CLEANUP] Проект удалён: {project_code}")
        except Exception as cleanup_error:
            logger.warning(f"[EXP_WARN] Ошибка при удалении проекта: {cleanup_error}")
        logger.close()
