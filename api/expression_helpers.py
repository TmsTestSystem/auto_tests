from typing import Dict, Any
import requests


def fetch_job_details(base_url: str, job_uuid: str, cookies: Dict[str, str]) -> Dict[str, Any]:
    url = f"{base_url}/api/jobs/details/{job_uuid}"
    response = requests.get(url, cookies=cookies, verify=False, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_job_payload(details_json: Dict[str, Any]) -> Dict[str, Any]:
    job_details = details_json
    if isinstance(details_json, dict):
        if 'job' in details_json:
            job_details = details_json['job']
        elif 'data' in details_json:
            job_details = details_json['data']
    return job_details

