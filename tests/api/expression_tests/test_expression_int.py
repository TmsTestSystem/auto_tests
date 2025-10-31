import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))

import pytest
import requests
import time
from api.file_panel_api import FilePanelAPI
from utils.custom_logger import setup_test_logger
from api.expression_helpers import fetch_job_details, extract_job_payload


@pytest.mark.usefixtures("expression_project")
def test_int_float(expression_project):
    logger = setup_test_logger("expression_int_test")
    logger.info("=" * 80)
    logger.info("[INT_TEST] Тест выражения int/int_float")
    logger.info("=" * 80)
    try:
        project_code, _ = expression_project
        file_panel_api = FilePanelAPI(project_code)
        base_url = file_panel_api.base_url
        cookies = file_panel_api.cookies
        path = "int/int_float.df.json"

        logger.info(f"[STEP 1] Вызов процесса: {path}")
        req_body = {
            "request_meta": {
                "object_id": "string",
                "request_id": "string",
                "tags": "string"
            },
            "request_data": {"value": 52.134}
        }
        url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={path}"
        response = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {url} -> {response.status_code}")

        assert response.status_code == 200, f"Статус ответа {response.status_code}: {response.text}"
        resp_json = response.json()
        assert resp_json.get("status") == "finished"
        assert resp_json.get("result", {}).get("data", {}).get("value") == 52
        job_uuid = resp_json.get("job_uuid")
        assert job_uuid, "job_uuid отсутствует в ответе вызова процесса"
        logger.info(f"[SUCCESS] Вызов процесса успешен: value=52, job_uuid={job_uuid}")

        logger.info("[STEP 2] Проверка деталей job")
        time.sleep(2)
        details_json = fetch_job_details(base_url, job_uuid, cookies)
        job_details = extract_job_payload(details_json)
        assert isinstance(job_details, dict), "Неверный формат ответа details"
        status_in_details = job_details.get("status") or details_json.get("status")
        assert status_in_details == "finished"
        result_obj = job_details.get("result") or details_json.get("result")
        assert isinstance(result_obj, dict), "Отсутствует объект result в деталях"
        assert result_obj.get("data", {}).get("value") == 52
        logger.info("[SUCCESS] Детали job корректны: status=finished, value=52")

        logger.info("[STEP 3] Юнит-тест диаграммы: ожидаем result=success")
        test_bp_url = f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={path}"
        payload_success = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "value"], "type": "equal", "value": 52}
                ]
            },
            "input_data": {"value": 52.134},
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

        logger.info("[STEP 4] Юнит-тест диаграммы: ожидаем result=checks_failed")
        payload_fail = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "value"], "type": "equal", "value": 53}
                ]
            },
            "input_data": {"value": 52.134},
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

        logger.info("[COMPLETE] Тест int/int_float завершён успешно")
    finally:
        logger.close()


@pytest.mark.usefixtures("expression_project")
def test_int_string(expression_project):
    logger = setup_test_logger("expression_int_test")
    logger.info("=" * 80)
    logger.info("[INT_TEST] Тест выражения int/int_string")
    logger.info("=" * 80)
    try:
        project_code, _ = expression_project
        file_panel_api = FilePanelAPI(project_code)
        base_url = file_panel_api.base_url
        cookies = file_panel_api.cookies
        path = "int/int_string.df.json"

        logger.info(f"[STEP 1] Вызов процесса: {path}")
        req_body = {
            "request_meta": {
                "object_id": "string",
                "request_id": "string",
                "tags": "string"
            },
            "request_data": {"value": "52.134"}
        }
        url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={path}"
        response = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {url} -> {response.status_code}")

        assert response.status_code == 200, f"Статус ответа {response.status_code}: {response.text}"
        resp_json = response.json()
        assert resp_json.get("status") == "finished"
        assert resp_json.get("result", {}).get("data", {}).get("value") == 52
        job_uuid = resp_json.get("job_uuid")
        assert job_uuid, "job_uuid отсутствует в ответе вызова процесса"
        logger.info(f"[SUCCESS] Вызов процесса успешен: value=52, job_uuid={job_uuid}")

        logger.info("[STEP 2] Проверка деталей job")
        time.sleep(2)
        details_json = fetch_job_details(base_url, job_uuid, cookies)
        job_details = extract_job_payload(details_json)
        assert isinstance(job_details, dict), "Неверный формат ответа details"
        status_in_details = job_details.get("status") or details_json.get("status")
        assert status_in_details == "finished"
        result_obj = job_details.get("result") or details_json.get("result")
        assert isinstance(result_obj, dict), "Отсутствует объект result в деталях"
        assert result_obj.get("data", {}).get("value") == 52
        logger.info("[SUCCESS] Детали job корректны: status=finished, value=52")

        logger.info("[STEP 3] Юнит-тест диаграммы: ожидаем result=success")
        test_bp_url = f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={path}"
        payload_success = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "value"], "type": "equal", "value": 52}
                ]
            },
            "input_data": {"value": "52.134"},
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

        logger.info("[STEP 4] Юнит-тест диаграммы: ожидаем result=checks_failed")
        payload_fail = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "value"], "type": "equal", "value": 51}
                ]
            },
            "input_data": {"value": "52.134"},
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

        logger.info("[COMPLETE] Тест int/int_string завершён успешно")
    finally:
        logger.close()


@pytest.mark.usefixtures("expression_project")
def test_int_string_error(expression_project):
    logger = setup_test_logger("expression_int_test")
    logger.info("=" * 80)
    logger.info("[INT_TEST] Тест выражения int/int_string_error (негативный)")
    logger.info("=" * 80)
    try:
        project_code, _ = expression_project
        file_panel_api = FilePanelAPI(project_code)
        base_url = file_panel_api.base_url
        cookies = file_panel_api.cookies
        path = "int/int_string_error.df.json"

        logger.info(f"[STEP 1] Вызов процесса (негатив): {path}")
        req_body = {
            "request_meta": {
                "object_id": "string",
                "request_id": "string",
                "tags": "string"
            },
            "request_data": {"value": "t+r"}
        }
        url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={path}"
        response = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {url} -> {response.status_code}")

        assert response.status_code == 200, f"Статус ответа {response.status_code}: {response.text}"
        resp_json = response.json()
        assert resp_json.get("status") == "error", f"Ожидали status=error, получили: {resp_json}"
        error_obj = (((resp_json or {}).get("result") or {}).get("error"))
        assert isinstance(error_obj, dict), "Ожидали объект error в result"
        logger.info(f"[INFO] error.message (call): {error_obj.get('message')}")
        assert error_obj.get("type"), "Отсутствует error.type"
        job_uuid = resp_json.get("job_uuid")
        assert job_uuid, "job_uuid отсутствует в ответе вызова процесса"
        logger.info(f"[SUCCESS] Вызов процесса вернул error: type={error_obj.get('type')}, job_uuid={job_uuid}")

        logger.info("[STEP 2] Проверка деталей job для негативного кейса")
        time.sleep(2)
        details_json = fetch_job_details(base_url, job_uuid, cookies)
        job_details = extract_job_payload(details_json)
        assert isinstance(job_details, dict), "Неверный формат ответа details"
        status_in_details = job_details.get("status") or details_json.get("status")
        assert status_in_details == "error", f"Ожидали status=error в деталях, получили: {details_json}"
        result_obj = job_details.get("result") or details_json.get("result")
        assert isinstance(result_obj, dict), "Отсутствует объект result в деталях"
        error_details = result_obj.get("error")
        assert isinstance(error_details, dict), "Отсутствует объект error в деталях"
        logger.info(f"[INFO] error.message (details): {error_details.get('message')}")
        error_type = error_details.get("type")
        assert error_type, "Отсутствует error.type в деталях"
        logger.info("[SUCCESS] Детали job корректны для негативного кейса: status=error, type совпадает")

        logger.info("[STEP 3] Юнит-тест диаграммы: ожидаем result=success (по error.type)")
        test_bp_url = f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={path}"
        payload_success = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["error", "type"], "type": "equal", "value": error_type}
                ]
            },
            "input_data": {"value": "t+r"},
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
        logger.info("[SUCCESS] test_bp success (негативный кейс) получен")

        logger.info("[STEP 4] Юнит-тест диаграммы: ожидаем result=checks_failed (по неверному error.type)")
        payload_fail = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["error", "type"], "type": "equal", "value": "SomeOtherType"}
                ]
            },
            "input_data": {"value": "t+r"},
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
        logger.info("[SUCCESS] test_bp checks_failed (негативный кейс) получен")

        logger.info("[COMPLETE] Тест int/int_string_error завершён успешно")
    finally:
        logger.close()

