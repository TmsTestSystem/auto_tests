"""
UI tests conftest - re-exports from root conftest
"""
import sys
from pathlib import Path
import pytest

# Добавляем корень проекта в sys.path для импорта корневого conftest
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Импортируем из корневого conftest
import importlib.util
root_conftest_path = root_path / "conftest.py"
spec = importlib.util.spec_from_file_location("root_conftest", root_conftest_path)
root_conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_conftest)

# Реэкспортируем функции для UI тестов
save_screenshot = root_conftest.save_screenshot
get_project_by_code = root_conftest.get_project_by_code
delete_project_by_id = root_conftest.delete_project_by_id
get_auth_cookies = root_conftest.get_auth_cookies
get_all_projects_via_api = root_conftest.get_all_projects_via_api
get_api_base_url = root_conftest.get_api_base_url
wait_for_canvas_with_refresh = root_conftest.wait_for_canvas_with_refresh

# Реэкспортируем фикстуры из корневого conftest
login_page = root_conftest.login_page
flow_project = root_conftest.flow_project

