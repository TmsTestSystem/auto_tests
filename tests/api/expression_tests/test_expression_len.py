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
def test_len_list(expression_project):
    logger = setup_test_logger("expression_len_test")
    logger.info("=" * 80)
    logger.info("[LEN_TEST] Тест выражения len/len_list")
    logger.info("=" * 80)
    try:
        project_code, _ = expression_project
        file_panel_api = FilePanelAPI(project_code)
        base_url = file_panel_api.base_url
        cookies = file_panel_api.cookies
        path = "len/len_list.df.json"

        # [STEP 1] Вызов процесса
        logger.info(f"[STEP 1] Вызов процесса: {path}")
        req_body = {
            "request_meta": {
                "object_id": "string",
                "request_id": "string",
                "tags": "string"
            },
            "request_data": {"data": [1, 2, 3, 4, 5, 6]}
        }
        url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={path}"
        response = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {url} -> {response.status_code}")

        assert response.status_code == 200, f"Статус ответа {response.status_code}: {response.text}"
        resp_json = response.json()
        assert resp_json.get("status") == "finished"
        assert resp_json.get("result", {}).get("data", {}).get("len_list") == 6
        job_uuid = resp_json.get("job_uuid")
        assert job_uuid, "job_uuid отсутствует в ответе вызова процесса"
        logger.info(f"[SUCCESS] Вызов процесса успешен: len_list=6, job_uuid={job_uuid}")

        # [STEP 2] Проверка лога выполнения по job_uuid
        logger.info("[STEP 2] Проверка деталей job")
        time.sleep(2)
        details_json = fetch_job_details(base_url, job_uuid, cookies)
        job_details = extract_job_payload(details_json)
        assert isinstance(job_details, dict), "Неверный формат ответа details"
        status_in_details = job_details.get("status") or details_json.get("status")
        assert status_in_details == "finished"
        result_obj = job_details.get("result") or details_json.get("result")
        assert isinstance(result_obj, dict), "Отсутствует объект result в деталях"
        assert result_obj.get("data", {}).get("len_list") == 6
        logger.info("[SUCCESS] Детали job корректны: status=finished, len_list=6")

        # [STEP 3] Unit-тест диаграммы (ожидаем success)
        logger.info("[STEP 3] Юнит-тест диаграммы: ожидаем result=success")
        test_bp_url = f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={path}"
        payload_success = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "len_list"], "type": "equal", "value": 6}
                ]
            },
            "input_data": {"data": [1, 2, 3, 4, 5, 6]},
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
                    {"field": None, "path": ["data", "len_list"], "type": "equal", "value": 7}
                ]
            },
            "input_data": {"data": [1, 2, 3, 4, 5, 6]},
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

        logger.info("[COMPLETE] Тест len/len_list завершён успешно")
    finally:
        logger.close()


@pytest.mark.usefixtures("expression_project")
def test_len_string(expression_project):
    logger = setup_test_logger("expression_len_test")
    logger.info("=" * 80)
    logger.info("[LEN_TEST] Тест выражения len/len_string")
    logger.info("=" * 80)
    try:
        project_code, _ = expression_project
        file_panel_api = FilePanelAPI(project_code)
        base_url = file_panel_api.base_url
        cookies = file_panel_api.cookies
        path = "len/len_string.df.json"

        # [STEP 1] Вызов процесса
        logger.info(f"[STEP 1] Вызов процесса: {path}")
        req_body = {
            "request_meta": {
                "object_id": "string",
                "request_id": "string",
                "tags": "string"
            },
            "request_data": {"data": "Test"}
        }
        url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={path}"
        response = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {url} -> {response.status_code}")

        assert response.status_code == 200, f"Статус ответа {response.status_code}: {response.text}"
        resp_json = response.json()
        assert resp_json.get("status") == "finished"
        assert resp_json.get("result", {}).get("data", {}).get("len_string") == 4
        job_uuid = resp_json.get("job_uuid")
        assert job_uuid, "job_uuid отсутствует в ответе вызова процесса"
        logger.info(f"[SUCCESS] Вызов процесса успешен: len_string=4, job_uuid={job_uuid}")

        # [STEP 2] Проверка лога выполнения по job_uuid
        logger.info("[STEP 2] Проверка деталей job")
        time.sleep(2)
        details_json = fetch_job_details(base_url, job_uuid, cookies)
        job_details = extract_job_payload(details_json)
        assert isinstance(job_details, dict), "Неверный формат ответа details"
        status_in_details = job_details.get("status") or details_json.get("status")
        assert status_in_details == "finished"
        result_obj = job_details.get("result") or details_json.get("result")
        assert isinstance(result_obj, dict), "Отсутствует объект result в деталях"
        assert result_obj.get("data", {}).get("len_string") == 4
        logger.info("[SUCCESS] Детали job корректны: status=finished, len_string=4")

        # [STEP 3] Unit-тест диаграммы (ожидаем success)
        logger.info("[STEP 3] Юнит-тест диаграммы: ожидаем result=success")
        test_bp_url = f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={path}"
        payload_success = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "len_string"], "type": "equal", "value": 4}
                ]
            },
            "input_data": {"data": "Test"},
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
                    {"field": None, "path": ["data", "len_string"], "type": "equal", "value": 5}
                ]
            },
            "input_data": {"data": "Test"},
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

        logger.info("[COMPLETE] Тест len/len_string завершён успешно")
    finally:
        logger.close()


@pytest.mark.usefixtures("expression_project")
def test_len_object(expression_project):
    logger = setup_test_logger("expression_len_test")
    logger.info("=" * 80)
    logger.info("[LEN_TEST] Тест выражения len/len_object")
    logger.info("=" * 80)
    try:
        project_code, _ = expression_project
        file_panel_api = FilePanelAPI(project_code)
        base_url = file_panel_api.base_url
        cookies = file_panel_api.cookies
        path = "len/len_object.df.json"

        # [STEP 1] Вызов процесса
        logger.info(f"[STEP 1] Вызов процесса: {path}")
        req_body = {
            "request_meta": {
                "object_id": "string",
                "request_id": "string",
                "tags": "string"
            },
            "request_data": {"data": {"a": 1, "b": 2, "c": 3}}
        }
        url = f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={path}"
        response = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=30)
        logger.info(f"[INFO] POST {url} -> {response.status_code}")

        assert response.status_code == 200, f"Статус ответа {response.status_code}: {response.text}"
        resp_json = response.json()
        assert resp_json.get("status") == "finished"
        assert resp_json.get("result", {}).get("data", {}).get("len_object") == 3
        job_uuid = resp_json.get("job_uuid")
        assert job_uuid, "job_uuid отсутствует в ответе вызова процесса"
        logger.info(f"[SUCCESS] Вызов процесса успешен: len_object=3, job_uuid={job_uuid}")

        # [STEP 2] Проверка лога выполнения по job_uuid
        logger.info("[STEP 2] Проверка деталей job")
        time.sleep(2)
        details_json = fetch_job_details(base_url, job_uuid, cookies)
        job_details = extract_job_payload(details_json)
        assert isinstance(job_details, dict), "Неверный формат ответа details"
        status_in_details = job_details.get("status") or details_json.get("status")
        assert status_in_details == "finished"
        result_obj = job_details.get("result") or details_json.get("result")
        assert isinstance(result_obj, dict), "Отсутствует объект result в деталях"
        assert result_obj.get("data", {}).get("len_object") == 3
        logger.info("[SUCCESS] Детали job корректны: status=finished, len_object=3")

        # [STEP 3] Unit-тест диаграммы (ожидаем success)
        logger.info("[STEP 3] Юнит-тест диаграммы: ожидаем result=success")
        test_bp_url = f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={path}"
        payload_success = {
            "checks": {
                "object_result_checks": [
                    {"field": None, "path": ["data", "len_object"], "type": "equal", "value": 3}
                ]
            },
            "input_data": {"data": {"a": 1, "b": 2, "c": 3}},
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
                    {"field": None, "path": ["data", "len_object"], "type": "equal", "value": 4}
                ]
            },
            "input_data": {"data": {"a": 1, "b": 2, "c": 3}},
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

        logger.info("[COMPLETE] Тест len/len_object завершён успешно")
    finally:
        logger.close()

