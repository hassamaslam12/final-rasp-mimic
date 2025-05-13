import os
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NOTIFICATION_API_BASEURL = os.getenv('NOTIFICATION_API_BASEURL')
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
NOTIFICATION_INTERVAL_MINUTES = int(os.getenv('NOTIFICATION_INTERVAL_MINUTES', 15))

# For tracking last notification times
_last_notification_times = {}
_retry_queue = []  # Each item: (retry_time, user_id, title, content, jwt_token, event_key)

RETRY_INTERVAL_MINUTES = 5

def queue_notification_retry(user_id, title, content, jwt_token, event_key):
    from datetime import datetime, timedelta
    retry_time = datetime.now() + timedelta(minutes=RETRY_INTERVAL_MINUTES)
    _retry_queue.append((retry_time, user_id, title, content, jwt_token, event_key))
    print(f"[Notification Retry Scheduled] {title} at {retry_time}")

def process_notification_retries():
    from datetime import datetime
    now = datetime.now()
    for item in _retry_queue[:]:
        retry_time, user_id, title, content, jwt_token, event_key = item
        if now >= retry_time:
            print(f"[Notification Retry Attempt] {title}")
            resp = send_notification(user_id, title, content, jwt_token, retry=True)
            if resp and resp.get("status") == "success":
                _retry_queue.remove(item)
                _last_notification_times[event_key] = now
            else:
                # reschedule for another 5 minutes
                _retry_queue.remove(item)
                queue_notification_retry(user_id, title, content, jwt_token, event_key)

def can_send_notification(event_key):
    """
    Returns True if a notification can be sent for the given event_key (e.g. 'hassam', 'unknown', 'temper'),
    based on the interval set in env. Otherwise, returns False.
    """
    now = datetime.now()
    last_time = _last_notification_times.get(event_key)
    if last_time is None or now - last_time > timedelta(minutes=NOTIFICATION_INTERVAL_MINUTES):
        _last_notification_times[event_key] = now
        return True
    return False

def send_notification(user_id, title, content, jwt_token, event_key=None, retry=False):
    url = f"{NOTIFICATION_API_BASEURL}/api/external-notifications/send"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "user_id": user_id,
        "title": title,
        "content": content
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        resp_json = response.json()
        if resp_json.get("status") == "success":
            print(f"[Notification Success] {resp_json}")
        return resp_json
    except Exception as e:
        print(f"Notification error: {e}")
        if not retry and event_key:
            queue_notification_retry(user_id, title, content, jwt_token, event_key)
        return None

