import sys
import uuid
import base64
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
                    "git_url": "/opt/app/empty_repo",
                    "default_branch": "master",
                    "gradient": "green",
                    "description": f"Проект для тестирования туториала {project_code}",
                    "git": "/opt/app/empty_repo"
                }
                
                response = requests.post(f"{base_url}/api/projects", json=create_data, cookies=cookies, verify=False, timeout=30)
                response.raise_for_status()
                project_info = response.json()
                logger.info(f"[TUTORIAL_SETUP] Проект туториала создан: {project_info}")
                
                yield project_code, project_info
                
            except Exception as e:
                logger.error(f"[TUTORIAL_ERROR] Не удалось создать проект туториала: {e}")
                raise
            
            try:
                if project_info:
                    requests.delete(f"{base_url}/api/projects/{project_info['id']}", cookies=cookies, verify=False, timeout=30)
                    logger.info(f"[TUTORIAL_CLEANUP] Проект туториала {project_code} удален")
            except Exception as cleanup_error:
                logger.warning(f"[TUTORIAL_WARN] Ошибка при удалении проекта туториала: {cleanup_error}")
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
            
            tutorial_files_dir = Path(__file__).parent.parent.parent.parent / "TutorialProcess"
            files_to_import = [
                ("tutorial_script.py", "/tutorial_script.py"),
                ("tutorial_success.test.json", "/tutorial_success.test.json"),
                ("TutorialProcess.df.json", "/TutorialProcess.df.json")
            ]
            
            for filename, import_path in files_to_import:
                file_path = tutorial_files_dir / filename
                
                if file_path.exists():
                    logger.info(f"[STEP] Импорт файла {filename}")
                    
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        content_base64 = base64.b64encode(file_content).decode()
                    
                    import_result = tutorial_file_panel_api.import_file(import_path, content_base64)
                    logger.info(f"[SUCCESS] Файл {filename} импортирован: {import_result}")
                    
                    read_result = tutorial_file_panel_api.read_file(import_path)
                    logger.info(f"[SUCCESS] Файл {filename} прочитан для проверки")
                else:
                    logger.warning(f"[WARNING] Файл {filename} не найден в {tutorial_files_dir}")
            
            logger.info("[STEP 6] Ожидание обработки файла процесса сервером...")
            import time
            time.sleep(3)
            
            logger.info("[STEP 7] Вызов процесса TutorialProcess.df.json")
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
            logger.info(f"[SUCCESS] Процесс выполнен, job_uuid: {job_uuid}")
            
            logger.info("[STEP] Ожидание завершения процесса...")
            time.sleep(2)
            
            logger.info("[STEP 8] Проверка результата процесса")
            assert result.get('status') == 'finished', f"Процесс не завершился успешно: {result.get('status')}"
            assert 'result' in result, "Отсутствует результат выполнения процесса"
            assert 'data' in result['result'], "Отсутствуют данные в результате"
            
            result_data = result['result']['data']
            assert 'customer_id' in result_data, "Отсутствует customer_id в результате"
            assert 'total_monthly_payment_RUR' in result_data, "Отсутствует total_monthly_payment_RUR в результате"
            
            logger.info("[SUCCESS] Результат выполнения:")
            logger.info(f"[SUCCESS]   - customer_id: {result_data['customer_id']}")
            logger.info(f"[SUCCESS]   - total_monthly_payment_RUR: {result_data['total_monthly_payment_RUR']}")
            logger.info(f"[SUCCESS]   - job_duration: {result.get('job_duration')}ms")
            
            assert result_data['customer_id'] == "4535464sdf", "Неверный customer_id в результате"
            assert isinstance(result_data['total_monthly_payment_RUR'], (int, float)), "total_monthly_payment_RUR должен быть числом"
            
            logger.info("[STEP 9] Мониторинг job")
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
            
            logger.info("[STEP 10] Получение деталей job")
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
            
            logger.info("[STEP 11] Получение событий job")
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