def build_bp_call_url(base_url: str, project_code: str, object_path: str) -> str:
    return f"{base_url}/api/ide/{project_code}/branch/master/bps/call?path={object_path}"


def build_bp_test_url(base_url: str, project_code: str, object_path: str) -> str:
    return f"{base_url}/api/ide/{project_code}/branch/master/tests/test_bp?object_path={object_path}"


def build_job_details_url(base_url: str, job_uuid: str) -> str:
    return f"{base_url}/api/jobs/details/{job_uuid}"


