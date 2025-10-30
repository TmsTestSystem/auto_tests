import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))

import pytest
import requests
import time
from api.file_panel_api import FilePanelAPI
from utils.custom_logger import setup_test_logger

@pytest.mark.usefixtures("expression_project")
def test_if_else_positive(expression_project):
    logger = setup_test_logger("expression_if_test")
    logger.info("=" * 80)
    logger.info("[IF_TEST] Тест выражения if/if_else_positive")
    logger.info("=" * 80)
    try:
        project_code, _ = expression_project
        file_panel_api = FilePanelAPI(project_code)
        base_url = file_panel_api.base_url
        cookies = file_panel_api.cookies
        path = "if/if_else_positive.df.json"

        # [STEP 1] Вызов процесса
        logger.info(f"[STEP 1] Вызов процесса: {path}")
        req_body = {
            "request_meta": {
                "object_id": "string",
                "request_id": "string",
                "tags": "string"
            },
            "request_data": {"age": 17}
        }
        url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={path}"
        response = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {url} -> {response.status_code}")

        assert response.status_code == 200, f"Статус ответа {response.status_code}: {response.text}"
        resp_json = response.json()
        assert resp_json.get("status") == "finished"
        assert resp_json.get("result", {}).get("data", {}).get("decision") == "REJECT"
        job_uuid = resp_json.get("job_uuid")
        assert job_uuid, "job_uuid отсутствует в ответе вызова процесса"
        logger.info(f"[SUCCESS] Вызов процесса успешен: decision=REJECT, job_uuid={job_uuid}")

        # [STEP 2] Проверка лога выполнения по job_uuid
        logger.info("[STEP 2] Проверка деталей job")
        time.sleep(3)
        details_url = f"{base_url}/api/jobs/details/{job_uuid}"
        details_resp = requests.get(details_url, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] GET {details_url} -> {details_resp.status_code}")
        assert details_resp.status_code == 200, f"Details ошибка {details_resp.status_code}: {details_resp.text}"
        details_json = details_resp.json()

        job_details = details_json
        if isinstance(details_json, dict):
            if 'job' in details_json:
                job_details = details_json['job']
            elif 'data' in details_json:
                job_details = details_json['data']

        assert isinstance(job_details, dict), "Неверный формат ответа details"
        assert job_details.get("status") == "finished"
        result_obj = job_details.get("result") or details_json.get("result") if isinstance(details_json, dict) else None
        assert isinstance(result_obj, dict), "Отсутствует объект result в деталях"
        assert result_obj.get("data", {}).get("decision") == "REJECT"
        logger.info("[SUCCESS] Детали job корректны: status=finished, decision=REJECT")

        # [STEP 3] Unit-тест диаграммы (ожидаем success)
        logger.info("[STEP 3] Юнит-тест диаграммы: ожидаем result=success")
        test_bp_url = f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={path}"
        payload_success = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "decision"], "type": "equal", "value": "REJECT"}
                ]
            },
            "input_data": {"age": 17},
            "input_meta": {},
            "mocks": [],
            "test_result": {},
            "title": ""
        }
        test_resp_ok = requests.post(test_bp_url, json=payload_success, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {test_bp_url} -> {test_resp_ok.status_code}")
        assert test_resp_ok.status_code == 200, f"test_bp (success) статус {test_resp_ok.status_code}: {test_resp_ok.text}"
        test_json_ok = test_resp_ok.json()
        assert test_json_ok.get("result") == "success", f"Ожидали result=success, получили: {test_json_ok}"
        logger.info("[SUCCESS] test_bp success получен")

        # [STEP 4] Unit-тест диаграммы (ожидаем checks_failed)
        logger.info("[STEP 4] Юнит-тест диаграммы: ожидаем result=checks_failed")
        payload_fail = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "decision"], "type": "equal", "value": "ACCEPT"}
                ]
            },
            "input_data": {"age": 17},
            "input_meta": {},
            "mocks": [],
            "test_result": {},
            "title": ""
        }
        test_resp_fail = requests.post(test_bp_url, json=payload_fail, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {test_bp_url} -> {test_resp_fail.status_code}")
        assert test_resp_fail.status_code == 200, f"test_bp (checks_failed) статус {test_resp_fail.status_code}: {test_resp_fail.text}"
        test_json_fail = test_resp_fail.json()
        assert test_json_fail.get("result") == "checks_failed", f"Ожидали result=checks_failed, получили: {test_json_fail}"
        logger.info("[SUCCESS] test_bp checks_failed получен")

        logger.info("[COMPLETE] Тест if/if_else_positive завершён успешно")
    finally:
        logger.close()
