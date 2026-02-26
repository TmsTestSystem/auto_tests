import sys
import uuid
import base64
import json
import requests
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))

from conftest import get_auth_cookies, get_api_base_url
from api.file_panel_api import FilePanelAPI
from api.project_process_log import ProjectProcessLogAPI
from custom_logger import setup_test_logger


class TestTutorialAPI:
    
    def setup_logging(self):
        return setup_test_logger("tutorial_test")
    
    @pytest.fixture(scope="session")
    def tutorial_project(self):
        logger = self.setup_logging()
        
        try:
            base_url = get_api_base_url()
            cookies = get_auth_cookies()
            
            unique_id = str(uuid.uuid4())[:8]
            project_title = f"Tutorial Project {unique_id}"
            project_code = f"tutorial_{unique_id}"
            
            logger.info(f"[TUTORIAL_SETUP] Создаем проект туториала: {project_code}")
            
            project_info = None
            try:
                create_data = {
                    "title": project_title,
                    "code": project_code,
                    "description": f"Проект для тестирования туториала {project_code}",
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
                logger.info(f"[TUTORIAL_SETUP] Проект туториала создан: {project_info}")

                yield project_code, project_info
                
            except Exception as e:
                logger.error(f"[TUTORIAL_ERROR] Не удалось создать проект туториала: {e}")
                raise
            
            # Удаление проекта отключено для ручной проверки
            logger.info(f"[TUTORIAL_INFO] Проект оставлен для ручной проверки: {project_code} (ID: {project_info.get('id') if project_info else 'N/A'})")
            # try:
            #     if project_info:
            #         requests.delete(f"{base_url}/api/projects/{project_info['id']}", cookies=cookies, verify=False, timeout=30)
            #         logger.info(f"[TUTORIAL_CLEANUP] Проект туториала {project_code} удален")
            # except Exception as cleanup_error:
            #     logger.warning(f"[TUTORIAL_WARN] Ошибка при удалении проекта туториала: {cleanup_error}")
        finally:
            logger.close()

    # Утилита для ручной очистки туториальных проектов на стенде
    # Ищет проекты, созданные тестом туториала, и удаляет их через API
    @staticmethod
    def clear_tutorial_projects():
        logger = setup_test_logger("tutorial_cleanup")
        try:
            base_url = get_api_base_url()
            cookies = get_auth_cookies()

            logger.info("[TUTORIAL_CLEAN] Получаем список всех проектов...")
            resp = requests.get(f"{base_url}/api/projects", cookies=cookies, verify=False, timeout=30)
            resp.raise_for_status()
            projects = resp.json()

            tutorial_projects = []
            for prj in projects:
                code = (prj.get("code") or "").lower()
                title = prj.get("title") or ""

                is_tutorial = (
                    code.startswith("tutorial_") or
                    title.startswith("Tutorial Project")
                )
                if is_tutorial:
                    tutorial_projects.append(prj)

            if not tutorial_projects:
                logger.info("[TUTORIAL_CLEAN] Проекты туториала не найдены")
                return

            logger.info(f"[TUTORIAL_CLEAN] Найдено {len(tutorial_projects)} туториальных проектов")

            deleted = 0
            for prj in tutorial_projects:
                try:
                    prj_id = prj.get("id")
                    prj_code = prj.get("code")
                    if not prj_id:
                        logger.warning(f"[TUTORIAL_WARN] У проекта {prj_code} отсутствует ID")
                        continue

                    del_resp = requests.delete(
                        f"{base_url}/api/projects/{prj_id}",
                        cookies=cookies,
                        verify=False,
                        timeout=30,
                    )
                    if del_resp.status_code in (200, 204):
                        deleted += 1
                        logger.info(f"[TUTORIAL_CLEAN] Удален проект: {prj_code}")
                    else:
                        logger.warning(
                            f"[TUTORIAL_WARN] API вернул {del_resp.status_code} при удалении {prj_code}: {del_resp.text}"
                        )
                except Exception as e:
                    logger.warning(f"[TUTORIAL_WARN] Ошибка при удалении проекта {prj.get('code')}: {e}")

            logger.info(f"[TUTORIAL_CLEAN] Удалено {deleted} из {len(tutorial_projects)} туториальных проектов")
        except Exception as e:
            logger.error(f"[TUTORIAL_ERROR] Ошибка при очистке туториальных проектов: {e}")
            raise
        finally:
            logger.close()
    
    @pytest.fixture(scope="session")
    def tutorial_file_panel_api(self, tutorial_project):
        project_code, project_info = tutorial_project
        
        print(f"[TUTORIAL_FILE_PANEL_SETUP] Используем проект туториала: {project_code}")
        file_panel = FilePanelAPI(project_code)
        
        yield file_panel
        
        print(f"[TUTORIAL_FILE_PANEL_CLEANUP] Тест туториала завершен для проекта: {project_code}")
    
    @pytest.fixture(scope="session")
    def tutorial_process_log_api(self, tutorial_project):
        project_code, project_info = tutorial_project
        
        print(f"[TUTORIAL_PROCESS_LOG_SETUP] Используем проект туториала для логов: {project_code}")
        process_log_api = ProjectProcessLogAPI(project_code)
        
        yield process_log_api
        
        print(f"[TUTORIAL_PROCESS_LOG_CLEANUP] Тест логов процессов завершен для проекта: {project_code}")
    
    def test_tutorial_end_to_end(self, tutorial_file_panel_api, tutorial_process_log_api):
        logger = self.setup_logging()
        logger.info("=" * 80)
        logger.info("[TUTORIAL_E2E] Полный цикл туториала")
        logger.info("=" * 80)
        
        try:
            logger.info("[STEP 1] Импорт структуры данных tutorial.ds.json")
            tutorial_content_base64 = "ewogICJjb21wb25lbnRzIjogewogICAgInNjaGVtYXMiOiB7CiAgICAgICJDdXN0b21lciI6IHsKICAgICAgICAicHJvcGVydGllcyI6IHsKICAgICAgICAgICJjdXN0b21lcl9pZCI6IHsKICAgICAgICAgICAgImRlc2NyaXB0aW9uIjogItC40LTQtdC90YLQuNGE0LjQutCw0YLQvtGAINC60LvQuNC10L3RgtCwIiwKICAgICAgICAgICAgInR5cGUiOiAic3RyaW5nIgogICAgICAgICAgfSwKICAgICAgICAgICJsb2FucyI6IHsKICAgICAgICAgICAgImRlc2NyaXB0aW9uIjogItC60YDQtdC00LjRgtGLIiwKICAgICAgICAgICAgIml0ZW1zIjogewogICAgICAgICAgICAgICIkcmVmIjogIiMvY29tcG9uZW50cy9zY2hlbWFzL0xvYW4iCiAgICAgICAgICAgIH0sCiAgICAgICAgICAgICJ0eXBlIjogImFycmF5IgogICAgICAgICAgfQogICAgICAgIH0sCiAgICAgICAgInR5cGUiOiAib2JqZWN0IgogICAgICB9LAogICAgICAiTG9hbiI6IHsKICAgICAgICAicHJvcGVydGllcyI6IHsKICAgICAgICAgICJjdXJyZW5jeSI6IHsKICAgICAgICAgICAgImRlc2NyaXB0aW9uIjogItCy0LDQu9GO0YLQsCIsCiAgICAgICAgICAgICJ0eXBlIjogInN0cmluZyIKICAgICAgICAgIH0sCiAgICAgICAgICAibW9udGhseV9wYXltZW50IjogewogICAgICAgICAgICAiZGVzY3JpcHRpb24iOiAi0LXQttC10LzQtdGB0Y/Rh9C90YvQuSDQv9C70LDRgtGR0LYiLAogICAgICAgICAgICAidHlwZSI6ICJudW1iZXIiCiAgICAgICAgICB9CiAgICAgICAgfSwKICAgICAgICAidHlwZSI6ICJvYmplY3QiCiAgICAgIH0sCiAgICAgICJSZXNwb25zZSI6IHsKICAgICAgICAicHJvcGVydGllcyI6IHsKICAgICAgICAgICJjdXN0b21lcl9pZCI6IHsKICAgICAgICAgICAgImRlc2NyaXB0aW9uIjogItC40LTQtdC90YLQuNGE0LjQutCw0YLQvtGAINC60LvQuNC10L3RgtCwIiwKICAgICAgICAgICAgInR5cGUiOiAic3RyaW5nIgogICAgICAgICAgfSwKICAgICAgICAgICJ0b3RhbF9tb250aGx5X3BheW1lbnRfUlVSIjogewogICAgICAgICAgICAiZGVzY3JpcHRpb24iOiAi0L7QsdGJ0LjQuSDQtdC20LXQvNC10YHRj9GH0L3Ri9C5INC/0LvQsNGC0ZHQtiwg0YDRg9CxIiwKICAgICAgICAgICAgInR5cGUiOiAibnVtYmVyIgogICAgICAgICAgfQogICAgICAgIH0sCiAgICAgICAgInR5cGUiOiAib2JqZWN0IgogICAgICB9CiAgICB9CiAgfSwKICAiaW5mbyI6IHsKICAgICJ0aXRsZSI6ICJEZWNpc2lvbiBGbG93IiwKICAgICJ2ZXJzaW9uIjogIjEuMC4wIgogIH0sCiAgIm9wZW5hcGkiOiAiMy4wLjAiLAogICJwYXRocyI6IHt9LAogICJzZXJ2ZXJzIjogW10KfQ=="
            
            import_result = tutorial_file_panel_api.import_file("/tutorial.ds.json", tutorial_content_base64)
            logger.info(f"[SUCCESS] Файл импортирован: {import_result}")
            
            logger.info("[STEP 2] Чтение импортированного файла")
            read_result = tutorial_file_panel_api.read_file("/tutorial.ds.json")
            logger.info(f"[SUCCESS] Файл прочитан: {read_result}")
            
            logger.info("[STEP 3] Генерация Python классов")
            generate_result = tutorial_file_panel_api.generate_python_classes("/tutorial.ds.json")
            logger.info(f"[SUCCESS] Python классы сгенерированы: {generate_result}")
            
            logger.info("[STEP 4] Проверка дерева файлов после генерации")
            tree_result = tutorial_file_panel_api.get_file_tree()
            logger.info("[SUCCESS] Дерево файлов получено")
            
            data_structures_found = False
            tutorial_folder_found = False
            models_folder_found = False
            
            items = tree_result if isinstance(tree_result, list) else tree_result.get('items', [])
            
            for item in items:
                if item.get('basename') == 'data_structures' and item.get('system_file_type') == 'ds_python':
                    data_structures_found = True
                    logger.info("[SUCCESS] Найдена папка data_structures с типом ds_python")
                    
                    for tutorial_item in item.get('items', []):
                        if tutorial_item.get('basename') == 'tutorial':
                            tutorial_folder_found = True
                            logger.info("[SUCCESS] Найдена папка tutorial")
                            
                            for models_item in tutorial_item.get('items', []):
                                if models_item.get('basename') == 'models':
                                    models_folder_found = True
                                    logger.info("[SUCCESS] Найдена папка models с Python файлами:")
                                    for py_file in models_item.get('items', []):
                                        logger.info(f"[SUCCESS]   - {py_file.get('basename')} ({py_file.get('size_in_bytes')} байт)")
                                    break
                            break
                    break
            
            assert data_structures_found, "Папка data_structures не найдена"
            assert tutorial_folder_found, "Папка tutorial не найдена"
            assert models_folder_found, "Папка models не найдена"
            
            logger.info("[STEP 5] Импорт остальных файлов туториала")

            # Файлы туториала лежат в папке TutorialProcess внутри репозитория (рядом с корнем проекта)
            tutorial_files_dir = Path(__file__).parent.parent.parent / "TutorialProcess"
            files_to_import = [
                ("tutorial_script.py", "/tutorial_script.py"),
                ("tutorial_success.test.json", "/tutorial_success.test.json"),
                ("TutorialProcess.df.json", "/TutorialProcess.df.json")
            ]
            
            for filename, import_path in files_to_import:
                file_path = tutorial_files_dir / filename
                logger.info(f"[STEP] Импорт файла {filename} из {file_path}")

                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    content_base64 = base64.b64encode(file_content).decode()

                import_result = tutorial_file_panel_api.import_file(import_path, content_base64)
                logger.info(f"[SUCCESS] Файл {filename} импортирован: {import_result}")

                read_result = tutorial_file_panel_api.read_file(import_path)
                logger.info(f"[SUCCESS] Файл {filename} прочитан для проверки")
            
            logger.info("[STEP 6] Ожидание обработки файла процесса сервером...")
            import time
            # Увеличиваем время ожидания для индексации Python модулей сервером
            logger.info("[INFO] Ожидание индексации Python модулей (10 секунд)...")
            time.sleep(10)
            
            logger.info("[STEP 7] ensure_exist для git-репозитория проекта")
            base_url = get_api_base_url()
            cookies = get_auth_cookies()
            project_code = tutorial_file_panel_api.project_code

            ensure_url = f"{base_url}/api/ide/{project_code}/branch/master/git/repository/ensure_exist"
            logger.info(f"[TUTORIAL] GET {ensure_url}")
            ensure_resp = requests.get(ensure_url, cookies=cookies, verify=False, timeout=60)
            logger.info(f"[TUTORIAL] ensure_exist -> {ensure_resp.status_code}: {ensure_resp.text[:500]}")
            assert ensure_resp.status_code == 200, (
                f"Ошибка ensure_exist: {ensure_resp.status_code}, {ensure_resp.text}"
            )

            logger.info("[STEP 8] Вызов процесса TutorialProcess.df.json")
            request_data = {
                "customer_id": "4535464sdf",
                "loans": [
                    {
                        "currency": "RUR",
                        "monthly_payment": 32300.2
                    },
                    {
                        "currency": "EUR",
                        "monthly_payment": 323.2
                    },
                    {
                        "currency": "USD",
                        "monthly_payment": 323.2
                    }
                ]
            }
            
            result = tutorial_process_log_api.call_process("TutorialProcess.df.json", request_data, "autotest_process")
            job_uuid = result.get('job_uuid')
            logger.info(f"[SUCCESS] Процесс вызван, job_uuid: {job_uuid}")
            logger.info(f"[DEBUG] Полный ответ от call_process: {result}")
            
            logger.info("[STEP] Ожидание завершения процесса...")
            # Ждем завершения процесса, проверяя статус через get_job_details
            max_attempts = 30
            attempt = 0
            while attempt < max_attempts:
                time.sleep(1)
                job_details = tutorial_process_log_api.get_job_details(job_uuid)
                # Обработка различных структур ответа
                if isinstance(job_details, dict):
                    if 'job' in job_details:
                        status = job_details['job'].get('status')
                    elif 'status' in job_details:
                        status = job_details.get('status')
                    else:
                        status = None
                else:
                    status = None
                
                if status == 'finished':
                    logger.info(f"[SUCCESS] Процесс завершен (попытка {attempt + 1})")
                    result = job_details
                    if 'job' in result:
                        result = result['job']
                    break
                elif status == 'error':
                    logger.error(f"[ERROR] Процесс завершился с ошибкой (попытка {attempt + 1})")
                    logger.error(f"[ERROR] Детали ошибки: {job_details}")
                    raise AssertionError(f"Процесс завершился с ошибкой: {job_details}")
                elif status is None:
                    logger.warning(f"[WARN] Статус не определен (попытка {attempt + 1}), структура: {list(job_details.keys()) if isinstance(job_details, dict) else type(job_details)}")
                
                attempt += 1
                if attempt % 5 == 0:
                    logger.info(f"[INFO] Ожидание завершения процесса... (попытка {attempt}/{max_attempts}, статус: {status})")
            
            if attempt >= max_attempts:
                raise AssertionError(f"Процесс не завершился за {max_attempts} секунд")
            
            logger.info("[STEP 9] Проверка результата процесса")
            assert result.get('status') == 'finished', f"Процесс не завершился успешно: {result.get('status')}"
            assert 'result' in result, f"Отсутствует результат выполнения процесса. Доступные ключи: {list(result.keys())}"
            
            # Обработка структуры результата
            result_obj = result['result']
            
            # Проверка на наличие ошибки
            if isinstance(result_obj, dict) and ('error' in result_obj or 'type' in result_obj or 'message' in result_obj):
                error_message = result_obj.get('message', 'Неизвестная ошибка')
                error_type = result_obj.get('type', 'Unknown')
                logger.error(f"[ERROR] Процесс завершился с ошибкой в результате:")
                logger.error(f"[ERROR]   - Тип ошибки: {error_type}")
                logger.error(f"[ERROR]   - Сообщение: {error_message}")
                if 'sub_errors' in result_obj:
                    logger.error(f"[ERROR]   - Дополнительные ошибки: {result_obj['sub_errors']}")
                if 'error_locations' in result_obj:
                    logger.error(f"[ERROR]   - Места ошибок: {result_obj['error_locations']}")
                raise AssertionError(f"Процесс завершился с ошибкой: {error_type} - {error_message}")
            
            if isinstance(result_obj, dict) and 'data' in result_obj:
                result_data = result_obj['data']
            elif isinstance(result_obj, dict):
                # Если result напрямую содержит данные
                result_data = result_obj
            else:
                raise AssertionError(f"Неожиданная структура результата: {result_obj}")
            
            logger.info(f"[DEBUG] result_data: {result_data}")
            assert 'customer_id' in result_data, f"Отсутствует customer_id в результате. Доступные ключи: {list(result_data.keys())}"
            assert 'total_monthly_payment_RUR' in result_data, "Отсутствует total_monthly_payment_RUR в результате"
            
            logger.info("[SUCCESS] Результат выполнения:")
            logger.info(f"[SUCCESS]   - customer_id: {result_data['customer_id']}")
            logger.info(f"[SUCCESS]   - total_monthly_payment_RUR: {result_data['total_monthly_payment_RUR']}")
            logger.info(f"[SUCCESS]   - job_duration: {result.get('job_duration')}ms")
            
            assert result_data['customer_id'] == "4535464sdf", "Неверный customer_id в результате"
            assert isinstance(result_data['total_monthly_payment_RUR'], (int, float)), "total_monthly_payment_RUR должен быть числом"
            
            logger.info("[STEP 10] Мониторинг job")
            jobs_result = tutorial_process_log_api.get_jobs(page=0, page_size=10)
            logger.info("[SUCCESS] Список jobs получен")
            
            job_found = False
            for job in jobs_result.get('jobs', []):
                if job.get('job_uuid') == job_uuid:
                    job_found = True
                    logger.info("[SUCCESS] Job найден в списке:")
                    logger.info(f"[SUCCESS]   - job_uuid: {job.get('job_uuid')}")
                    logger.info(f"[SUCCESS]   - object_id: {job.get('object_id')}")
                    logger.info(f"[SUCCESS]   - status: {job.get('status')}")
                    logger.info(f"[SUCCESS]   - project_code: {job.get('project_code')}")
                    break
            
            assert job_found, f"Job {job_uuid} не найден в списке jobs"
            
            logger.info("[STEP 11] Получение деталей job")
            job_details_response = tutorial_process_log_api.get_job_details(job_uuid)
            logger.info("[SUCCESS] Детали job получены")
            
            assert job_details_response is not None, "Детали job не получены"
            logger.info(f"[SUCCESS] Детали job получены (содержат {len(job_details_response)} полей)")
            
            logger.info(f"[SUCCESS] Проверяем доступные поля в деталях job: {list(job_details_response.keys())}")
            
            # Извлекаем данные job из ответа (может быть вложенная структура)
            job_details = job_details_response
            if 'job' in job_details_response:
                job_details = job_details_response['job']
            elif 'data' in job_details_response:
                job_details = job_details_response['data']
            
            logger.info(f"[SUCCESS] Извлеченные данные job: {list(job_details.keys()) if isinstance(job_details, dict) else 'не словарь'}")
            
            if isinstance(job_details, dict):
                if 'status' in job_details:
                    assert job_details.get('status') == "finished", f"Job не завершен: {job_details.get('status')}"
                    logger.info(f"[SUCCESS] Статус job: {job_details.get('status')}")
                
                if 'job_uuid' in job_details:
                    assert job_details.get('job_uuid') == job_uuid, "Неверный job_uuid в деталях"
                    logger.info(f"[SUCCESS] job_uuid в деталях: {job_details.get('job_uuid')}")
                
                if 'object_id' in job_details:
                    assert job_details.get('object_id') == "autotest_process", "Неверный object_id в деталях"
                    logger.info(f"[SUCCESS] object_id в деталях: {job_details.get('object_id')}")
                
                logger.info("[SUCCESS] Детали job:")
                logger.info(f"[SUCCESS]   - object_id: {job_details.get('object_id', 'не найден')}")
                logger.info(f"[SUCCESS]   - status: {job_details.get('status', 'не найден')}")
                logger.info(f"[SUCCESS]   - project_code: {job_details.get('project_code', 'не найден')}")
                logger.info(f"[SUCCESS]   - job_duration: {job_details.get('job_duration', 'не найден')}ms")
                logger.info(f"[SUCCESS]   - job_uuid: {job_details.get('job_uuid', 'не найден')}")
            else:
                logger.info(f"[SUCCESS] Детали job (не словарь): {job_details}")
            
            logger.info("[STEP 12] Получение событий job")
            job_events = tutorial_process_log_api.get_job_events(job_uuid)
            logger.info("[SUCCESS] События job получены")
            
            assert isinstance(job_events, (list, dict)), "События должны быть списком или словарем"
            logger.info(f"[SUCCESS] События job получены (тип: {type(job_events)})")
            
            if isinstance(job_events, list):
                logger.info(f"[SUCCESS] Количество событий: {len(job_events)}")
                for i, event in enumerate(job_events[:3]):
                    logger.info(f"[SUCCESS]   Событие {i+1}: {event}")
            elif isinstance(job_events, dict):
                logger.info(f"[SUCCESS] События в формате словаря: {list(job_events.keys())}")
            
            logger.info("[COMPLETE] Полный end-to-end тест туториала выполнен успешно!")
            
        except Exception as e:
            logger.error(f"[ERROR] Ошибка в end-to-end тесте туториала: {e}")
            raise
        finally:
            logger.close()