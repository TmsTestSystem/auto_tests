"""
API методы для работы с логами процессов и jobs
"""

import requests
import urllib3
import time
from typing import Dict, Any
from conftest import get_auth_cookies, get_api_base_url

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ProjectProcessLogAPI:
    """API методы для работы с логами процессов и jobs"""
    
    def __init__(self, project_code: str, branch: str = "master"):
        self.project_code = project_code
        self.branch = branch
        self.base_url = get_api_base_url()
        self.cookies = get_auth_cookies()
    
    def call_process(self, process_path: str, request_data: Dict[str, Any], object_id: str = "autotest_process") -> Dict[str, Any]:
        """
        Вызвать процесс (decision flow)
        
        Args:
            process_path: Путь к файлу процесса (.df.json)
            request_data: Данные для выполнения процесса
            object_id: ID объекта (тег)
            
        Returns:
            Dict с результатом выполнения процесса
        """
        url = f"{self.base_url}/api/ide/{self.project_code}/branch/{self.branch}/bps/call"
        
        params = {
            "path": process_path
        }
        
        data = {
            "request_meta": {
                "object_id": object_id,
                "request_id": f"test_{object_id}_{int(time.time())}",
                "tags": object_id
            },
            "request_data": request_data
        }
        
        try:
            response = requests.post(url, params=params, json=data, cookies=self.cookies, verify=False, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при вызове процесса {process_path}: {e}")
            raise
    
    def get_jobs(self, page: int = 0, page_size: int = 10, project: str = None) -> Dict[str, Any]:
        """
        Получить список jobs
        
        Args:
            page: Номер страницы
            page_size: Размер страницы
            project: Код проекта (если не указан, используется текущий)
            
        Returns:
            Dict со списком jobs
        """
        if project is None:
            project = self.project_code
            
        url = f"{self.base_url}/api/jobs"
        
        params = {
            "page": page,
            "page_size": page_size,
            "project": project
        }
        
        try:
            response = requests.get(url, params=params, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при получении списка jobs: {e}")
            raise
    
    def get_job_details(self, job_uuid: str) -> Dict[str, Any]:
        """
        Получить детали job по UUID
        
        Args:
            job_uuid: UUID job
            
        Returns:
            Dict с деталями job
        """
        url = f"{self.base_url}/api/jobs/details/{job_uuid}"
        
        try:
            response = requests.get(url, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при получении деталей job {job_uuid}: {e}")
            raise
    
    def get_job_events(self, job_uuid: str) -> Dict[str, Any]:
        """
        Получить события job по UUID
        
        Args:
            job_uuid: UUID job
            
        Returns:
            Dict с событиями job
        """
        url = f"{self.base_url}/api/events/{job_uuid}"
        
        try:
            response = requests.get(url, cookies=self.cookies, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при получении событий job {job_uuid}: {e}")
            raise
