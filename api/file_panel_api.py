"""
API методы для работы с файловой панелью
"""

import json
import requests
import urllib3
from typing import Any, Dict, List, Optional, Union
from conftest import get_auth_cookies, get_api_base_url

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FilePanelAPI:
    """API методы для работы с файловой панелью"""
    
    def __init__(self, project_code: str, branch: str = "master"):
        """
        Инициализация API для файловой панели
        
        Args:
            project_code: Код проекта
            branch: Ветка проекта (по умолчанию master)
        """
        self.project_code = project_code
        self.branch = branch
        self.base_url = get_api_base_url()
        self.cookies = get_auth_cookies()
        
        self.api_base = f"{self.base_url}/api/ide/{project_code}/branch/{branch}"
    
    def get_file_tree(self) -> Dict[str, Any]:
        """
        Получить дерево файлов проекта
        
        Returns:
            Dict с информацией о файлах и папках
        """
        url = f"{self.api_base}/files/tree?"
        
        try:
            response = requests.get(url, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при получении дерева файлов: {e}")
            raise
    
    def create_folder(self, folder_name: str, parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать папку
        
        Args:
            folder_name: Имя папки
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданной папке
        """
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{folder_name}",
            "type": "directory"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании папки {folder_name}: {e}")
            raise
    
    def create_file(self, file_name: str, content: str = "", parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать файл
        
        Args:
            file_name: Имя файла
            content: Содержимое файла
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданном файле
        """
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{file_name}",
            "type": "file"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании файла {file_name}: {e}")
            raise
    
    def get_file_content(self, file_path: str) -> str:
        """
        Получить содержимое файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Содержимое файла
        """
        url = f"{self.api_base}/files/read"
        
        params = {
            "path": file_path
        }
        
        try:
            response = requests.get(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            # Ответ files/read: text/plain; charset=utf-8 (тело — текст файла, не JSON)
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при получении содержимого файла {file_path}: {e}")
            raise
    
    def update_file_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Обновить содержимое файла
        
        Args:
            file_path: Путь к файлу
            content: Новое содержимое файла
            
        Returns:
            Dict с результатом операции
        """
        url = f"{self.api_base}/files/content"
        
        data = {
            "path": file_path,
            "content": content
        }
        
        try:
            response = requests.put(url, json=data, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при обновлении файла {file_path}: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """
        Удалить файл
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл удален успешно
        """
        url = f"{self.api_base}/files/delete"
        
        params = {
            "path": file_path
        }
        
        try:
            response = requests.delete(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            print(f"[DEBUG] Статус код удаления файла: {response.status_code}")
            response.raise_for_status()
            return response.status_code in [200, 204]
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при удалении файла {file_path}: {e}")
            raise
    
    def delete_folder(self, folder_path: str) -> bool:
        """
        Удалить папку
        
        Args:
            folder_path: Путь к папке
            
        Returns:
            True если папка удалена успешно
        """
        url = f"{self.api_base}/files/delete"
        
        params = {
            "path": folder_path
        }
        
        try:
            response = requests.delete(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.status_code in [200, 204]
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при удалении папки {folder_path}: {e}")
            raise
    
    def rename_file(self, old_path: str, new_name: str) -> Dict[str, Any]:
        """
        Переименовать файл
        
        Args:
            old_path: Текущий путь к файлу
            new_name: Новое имя файла
            
        Returns:
            Dict с результатом операции
        """
        url = f"{self.api_base}/files/rename"
        
        params = {
            "path": old_path
        }
        
        data = {
            "path": new_name
        }
        
        try:
            response = requests.patch(url, params=params, json=data, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при переименовании файла {old_path}: {e}")
            raise
    
    def move_file(self, file_path: str, new_parent_path: str) -> Dict[str, Any]:
        """
        Переместить файл
        
        Args:
            file_path: Путь к файлу
            new_parent_path: Новый родительский путь
            
        Returns:
            Dict с результатом операции
        """
        url = f"{self.api_base}/files/move"
        
        data = {
            "file_path": file_path,
            "new_parent_path": new_parent_path
        }
        
        try:
            response = requests.put(url, json=data, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при перемещении файла {file_path}: {e}")
            raise
    
    def upload_file(self, file_path: str, file_content: bytes, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        """
        Загрузить файл
        
        Args:
            file_path: Путь для сохранения файла
            file_content: Содержимое файла в байтах
            content_type: MIME тип файла
            
        Returns:
            Dict с результатом операции
        """
        url = f"{self.api_base}/files/upload"
        
        files = {
            'file': (file_path.split('/')[-1], file_content, content_type)
        }
        
        data = {
            'path': file_path
        }
        
        try:
            response = requests.post(url, files=files, data=data, cookies=self.cookies, verify=False, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при загрузке файла {file_path}: {e}")
            raise
    
    def import_file(self, file_path: str, content_base64: str) -> Dict[str, Any]:
        """
        Импортировать файл с содержимым в base64
        
        Args:
            file_path: Путь к файлу для импорта
            content_base64: Содержимое файла в base64
            
        Returns:
            Dict с результатом импорта
        """
        url = f"{self.api_base}/files/import"
        
        params = {
            "path": file_path
        }
        
        data = {
            "content": content_base64
        }
        
        try:
            response = requests.post(url, params=params, json=data, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при импорте файла {file_path}: {e}")
            raise
    
    def read_file(self, file_path: str) -> Union[str, Dict[str, Any], List[Any]]:
        """
        Прочитать содержимое файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Для .json (или application/json) — распарсенный JSON (dict/list).
            Иначе — текст файла в UTF-8 (как отдаёт files/read: text/plain).
        """
        url = f"{self.api_base}/files/read"
        
        params = {
            "path": file_path
        }
        
        try:
            response = requests.get(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            text = response.text
            ct = (response.headers.get("Content-Type") or "").lower()
            if "application/json" in ct:
                if not text.strip():
                    return {}
                return json.loads(text)
            basename = file_path.rstrip("/").rsplit("/", 1)[-1].lower()
            if basename.endswith(".json"):
                if not text:
                    return {}
                return json.loads(text)
            return text
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при чтении файла {file_path}: {e}")
            raise
    
    def generate_python_classes(self, data_structure_path: str) -> Dict[str, Any]:
        """
        Сгенерировать Python классы для структуры данных
        
        Args:
            data_structure_path: Путь к файлу структуры данных
            
        Returns:
            Dict с сгенерированными Python классами
        """
        url = f"{self.api_base}/data_structures/generate"
        
        params = {
            "path": data_structure_path
        }
        
        try:
            response = requests.get(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при генерации Python классов для {data_structure_path}: {e}")
            raise
    
        """
        Получить статус git репозитория
        
        Returns:
            Dict с информацией о статусе git репозитория
        """
        url = f"{self.base_url}/api/ide/{self.project_code}/git/index/{self.branch}/status"
        
        try:
            response = requests.get(url, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при получении статуса git: {e}")
            raise
    
    def get_file_tree_light(self, system_file_type: str = None) -> Dict[str, Any]:
        """
        Получить легкое дерево файлов с возможностью фильтрации по типу
        
        Args:
            system_file_type: Тип файла для фильтрации (например, 'data_structure')
            
        Returns:
            Dict с информацией о файлах и папках
        """
        url = f"{self.api_base}/files/tree_light?"
        
        params = {}
        if system_file_type:
            params['system_file_type'] = system_file_type
        
        try:
            response = requests.get(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при получении легкого дерева файлов: {e}")
            raise
    
    def create_process_file(self, process_name: str, parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать файл процесса
        
        Args:
            process_name: Имя процесса (без расширения .df.json)
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданном файле процесса
        """
        if not process_name.endswith('.df.json'):
            process_name = f"{process_name}.df.json"
        
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{process_name}",
            "type": "file"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании файла процесса {process_name}: {e}")
            raise
    
    def create_data_structure_file(self, structure_name: str, parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать файл структуры данных
        
        Args:
            structure_name: Имя структуры (без расширения .ds.json)
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданном файле структуры данных
        """
        if not structure_name.endswith('.ds.json'):
            structure_name = f"{structure_name}.ds.json"
        
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{structure_name}",
            "type": "file"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании файла структуры данных {structure_name}: {e}")
            raise
    
    def create_db_connection_file(self, db_name: str, parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать файл подключения к БД
        
        Args:
            db_name: Имя подключения к БД (без расширения .db.json)
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданном файле подключения к БД
        """
        if not db_name.endswith('.db.json'):
            db_name = f"{db_name}.db.json"
        
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{db_name}",
            "type": "file"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании файла подключения к БД {db_name}: {e}")
            raise
    
    def create_decision_table_file(self, table_name: str, parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать файл таблицы принятия решений
        
        Args:
            table_name: Имя таблицы принятия решений (без расширения .dt.json)
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданном файле таблицы принятия решений
        """
        if not table_name.endswith('.dt.json'):
            table_name = f"{table_name}.dt.json"
        
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{table_name}",
            "type": "file"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании файла таблицы принятия решений {table_name}: {e}")
            raise
    
    def create_python_script_file(self, script_name: str, parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать Python скрипт
        
        Args:
            script_name: Имя Python скрипта (без расширения .py)
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданном Python скрипте
        """
        if not script_name.endswith('.py'):
            script_name = f"{script_name}.py"
        
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{script_name}",
            "type": "file"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании Python скрипта {script_name}: {e}")
            raise
    
    def create_test_file(self, test_name: str, parent_path: str = "/") -> Dict[str, Any]:
        """
        Создать файл тестов
        
        Args:
            test_name: Имя теста (без расширения .test.json)
            parent_path: Путь к родительской папке
            
        Returns:
            Dict с информацией о созданном файле тестов
        """
        if not test_name.endswith('.test.json'):
            test_name = f"{test_name}.test.json"
        
        url = f"{self.api_base}/files/new"
        
        params = {
            "path": f"{parent_path}{test_name}",
            "type": "file"
        }
        
        try:
            response = requests.post(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при создании файла тестов {test_name}: {e}")
            raise
