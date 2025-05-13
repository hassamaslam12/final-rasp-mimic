import os
import requests
from dotenv import load_dotenv

load_dotenv()

FACES_API_BASEURL = os.getenv('FACES_API_BASEURL', os.getenv('NOTIFICATION_API_BASEURL'))
FACES_API_EMAIL = os.getenv('NOTIFICATION_EMAIL')
JWT_TOKEN = os.getenv('NOTIFICATION_JWT_TOKEN', 'YOUR_JWT_TOKEN_HERE')

# This will store face encodings and names after fetching once
faces_cache = {
    'encodings': [],
    'names': []
}

def fetch_faces():
    """
    Fetches all registered faces for the configured user (by email) and stores their encodings and names in faces_cache.
    """
    url = f"{FACES_API_BASEURL}/faces/list"
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    body = {"email": FACES_API_EMAIL}
    try:
        response = requests.get(url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)
        if data.get('data') and data['data'].get('faces'):
            faces = data['data']['faces']
            # Parse encodings from base64
            from main import base64_to_nparray
            faces_cache['encodings'] = [base64_to_nparray(f['face_encoding']) for f in faces if 'face_encoding' in f]
            faces_cache['names'] = [f['name'] for f in faces]
            print(f"[Faces API] Loaded {len(faces)} faces: {[f['name'] for f in faces]}")
        else:
            print("[Faces API] No faces found for this user.")
    except Exception as e:
        print(f"[Faces API] Error fetching faces: {e}")
        faces_cache['encodings'] = []
        faces_cache['names'] = []
