import time
import pytz
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = 'https://api.ucloudbiz.olleh.com/gd1'

def main(args: Dict[str, str]) -> Dict[str, str]:
    """
    Main function to manage NAS snapshots.
    """
    user = args['user']
    pwd = args['pwd']
    nasname = args['nasname']

    try:
        auth = get_token(user, pwd)
        project_id = get_project_id(auth)
        snapshots = get_nas_snapshots(auth, project_id)

        if len(snapshots) < 2:
            nas_id = get_nas_id(auth, project_id, nasname)
            status_code = create_nas_snapshot(auth, project_id, nasname, nas_id)
            return {"result": f"Created processing... Status code: {status_code}"}
        else:
            expired_snapshot_ids = get_expired_snapshot_ids(snapshots)
            if not expired_snapshot_ids:
                return {"result": "No expired snapshot"}
            else:
                delete_expired_snapshots(auth, project_id, expired_snapshot_ids)
                return {"result": "Delete processed"}
    except Exception as e:
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

def get_token(user: str, pwd: str) -> str:
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
    return response.headers['X-Subject-Token']

def get_project_id(auth: str) -> str:
    """
    Get the project ID.
    """
    url = f'{BASE_URL}/nc/Network'
    response = make_get_request(auth, url).json()
    return response['nc_listosnetworksresponse']['networks'][0]['projectid']

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
    Get IDs of expired snapshots.
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