import time
import pytz
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

BASE_URL = 'https://api.ucloudbiz.olleh.com/gd1'


def main(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    여러 NAS 에 대해 스냅샷을 관리하는 메인 함수.
    args["nasname"] 는 str 또는 List[str] 둘 다 허용.
    """
    user = args['user']
    pwd = args['pwd']
    nasnames_arg = args['nasname']

    # nasname 이 str 로 들어와도 리스트로 통일해서 처리
    if isinstance(nasnames_arg, str):
        nasnames: List[str] = [nasnames_arg]
    else:
        nasnames = list(nasnames_arg)

    try:
        api_result = get_token(user, pwd)
        auth = api_result.headers['X-Subject-Token']
        project_id = api_result.json()['token']['project']['id']

        # 스냅샷 리스트는 한 번만 조회
        all_snapshots = get_nas_snapshots(auth, project_id)
        print("All snapshots:", all_snapshots)

        results: Dict[str, str] = {}

        for nasname in nasnames:
            try:
                nas_id = get_nas_id(auth, project_id, nasname)
                if not nas_id:
                    results[nasname] = "NAS not found"
                    continue

                # 해당 NAS 의 스냅샷만 필터링
                snapshots_for_nas = [
                    s for s in all_snapshots
                    if s.get("share_id") == nas_id
                ]

                if len(snapshots_for_nas) < 2:
                    status_code = create_nas_snapshot(auth, project_id, nasname, nas_id)
                    results[nasname] = f"Created snapshot (status: {status_code})"
                else:
                    expired_snapshot_ids = get_expired_snapshot_ids(snapshots_for_nas)
                    if not expired_snapshot_ids:
                        results[nasname] = "No expired snapshot"
                    else:
                        delete_expired_snapshots(auth, project_id, expired_snapshot_ids)
                        results[nasname] = f"Deleted {len(expired_snapshot_ids)} expired snapshot(s)"
            except Exception as e:
                # NAS 개별 처리 중 에러는 개별 NAS 에 대한 결과로 남김
                results[nasname] = f"Error: {e}"

        return {"result": results}

    except Exception as e:
        # 토큰 발급 등 전체 처리 중 에러
        return {"error": str(e)}


def create_nas_snapshot(auth: str, project_id: str, nasname: str, nas_id: str) -> int:
    """
    Create a NAS snapshot.
    """
    url = f'{BASE_URL}/nas/{project_id}/snapshots'

    createtime = datetime.now().strftime("%y%m%d-%H:%M")
    data = {
        "snapshot": {
            "name": f"{createtime}-{nasname}-snapshot",
            "share_id": nas_id,
            "force": "True",
            "description": ""
        }
    }
    response = make_post_request(auth, url, data)
    return response.status_code


def make_post_request(auth: str, url: str, data: Dict) -> requests.Response:
    """
    Make a POST request.
    """
    headers = {"Content-Type": "application/json", "X-Auth-Token": auth}
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response


def make_get_request(auth: str, url: str) -> requests.Response:
    """
    Make a GET request.
    """
    headers = {"Content-Type": "application/json", "X-Auth-Token": auth}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response


def make_delete_request(auth: str, url: str) -> requests.Response:
    """
    Make a DELETE request.
    """
    headers = {"Content-Type": "application/json", "X-Auth-Token": auth}
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response


def get_token(user: str, pwd: str) -> requests.Response:
    """
    Get an authentication token.
    """
    url = f'{BASE_URL}/identity/auth/tokens'
    headers = {"Content-Type": "application/json"}
    data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "domain": {"id": "default"},
                        "name": user,
                        "password": pwd
                    }
                }
            },
            "scope": {
                "project": {
                    "domain": {"id": "default"},
                    "name": user
                }
            }
        }
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response


def get_nas_id(auth: str, project_id: str, nasname: str) -> Optional[str]:
    """
    Get the NAS ID.
    """
    url = f'{BASE_URL}/nas/{project_id}/shares'
    shares = make_get_request(auth, url).json()['shares']
    return next((share["id"] for share in shares if share["name"] == nasname), None)


def get_nas_snapshots(auth: str, project_id: str) -> List[Dict]:
    """
    Get the list of NAS snapshots.
    """
    url = f'{BASE_URL}/nas/{project_id}/snapshots/detail'
    response = make_get_request(auth, url).json()
    return response['snapshots']


def get_expired_snapshot_ids(snapshots: List[Dict]) -> List[str]:
    """
    Get IDs of expired snapshots (older than 2 weeks).
    """
    current_time = datetime.now()
    expired_date = current_time - timedelta(weeks=2)
    local_timezone = pytz.timezone('Asia/Seoul')
    utc_timezone = pytz.UTC
    expired_ids = []

    for snapshot in snapshots:
        created_at = datetime.strptime(snapshot["created_at"], "%Y-%m-%dT%H:%M:%S.%f")
        created_at = local_timezone.localize(created_at)
        created_at_utc = created_at.astimezone(utc_timezone)
        if created_at_utc < expired_date.replace(tzinfo=utc_timezone):
            expired_ids.append(snapshot["id"])

    return expired_ids


def delete_expired_snapshots(auth: str, project_id: str, snapshot_ids: List[str]) -> None:
    """
    Delete expired snapshots.
    """
    for snapshot_id in snapshot_ids:
        url = f'{BASE_URL}/nas/{project_id}/snapshots/{snapshot_id}'
        make_delete_request(auth, url)
        time.sleep(1)