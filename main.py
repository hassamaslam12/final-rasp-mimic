import cv2
import numpy as np
import face_recognition
from constants import CONFIDENCE_THRESHOLD

import base64
from notification_utils import send_notification, can_send_notification, process_notification_retries
from faces_api import fetch_faces, faces_cache
import os
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
JWT_TOKEN = os.getenv('NOTIFICATION_JWT_TOKEN', 'YOUR_JWT_TOKEN_HERE')

def base64_to_nparray(b64_string):
    decoded = base64.b64decode(b64_string)
    arr = np.frombuffer(decoded, dtype=np.float64)
    return arr


def get_location():
    """
    Returns a (latitude, longitude) tuple using ipinfo.io.
    Prints the result for debugging.
    """
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            loc = data.get("loc")
            if loc:
                lat, lon = loc.split(",")
                print(f"Fetched location: lat={lat}, lon={lon}")
                return lat, lon
            else:
                print("Location not found in response.")
        else:
            print(f"Location fetch failed: status {resp.status_code}")
    except Exception as e:
        print(f"Location fetch error: {e}")
    print("Fetched location: lat=None, lon=None")
    return None, None


def main():
    # Fetch faces once at the start, retry on failure
    import time
    while True:
        try:
            fetch_faces()
            # If faces_cache is populated, break
            if faces_cache['encodings'] and faces_cache['names']:
                break
            else:
                print("Faces API returned no faces, retrying in 3 seconds...")
        except Exception as e:
            print(f"Error fetching faces: {e}. Retrying in 3 seconds...")
        time.sleep(3)

    video_capture = cv2.VideoCapture(0)
    while not video_capture.isOpened():
        print("Error: Could not open webcam. Retrying in 3 seconds...")
        time.sleep(3)
        video_capture = cv2.VideoCapture(0)

    print("Starting camera. Press 'q' to quit.")

    prev_gray = None
    movement_threshold = 5000  # Tune as needed

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame. Attempting to restart camera...")
            if can_send_notification('camera_off'):
                lat, lon = get_location()
                if lat and lon:
                    extra_info = f" Location: lat={lat}, lon={lon}"
                    send_notification(NOTIFICATION_EMAIL, "Camera Off", f"Camera is off or cannot grab frame.{extra_info}", JWT_TOKEN, event_key='camera_off')
                else:
                    send_notification(NOTIFICATION_EMAIL, "Camera Off", "Camera is off or cannot grab frame.", JWT_TOKEN, event_key='camera_off')
            video_capture.release()
            import time
            time.sleep(2)
            video_capture = cv2.VideoCapture(0)
            continue

        # Movement detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        movement_detected = False
        if prev_gray is not None:
            frame_delta = cv2.absdiff(prev_gray, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            movement = cv2.countNonZero(thresh)
            if movement > movement_threshold:
                movement_detected = True
        prev_gray = gray

        # Check if the frame is black (all pixels are very dark)
        if np.mean(frame) < 10:  # Threshold can be adjusted if needed
            print("Temper alert: camera screen is black")
            if can_send_notification('temper'):
                lat, lon = get_location()
                if lat and lon:
                    extra_info = f" Location: lat={lat}, lon={lon}"
                    send_notification(NOTIFICATION_EMAIL, "Temper Alert", f"Camera screen is black (possible tampering).{extra_info}", JWT_TOKEN, event_key='temper')
                else:
                    send_notification(NOTIFICATION_EMAIL, "Temper Alert", "Camera screen is black (possible tampering).", JWT_TOKEN, event_key='temper')
            cv2.imshow('Facial Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        rgb_frame = frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Only send movement notification if there are no faces
        if movement_detected and len(face_locations) == 0:
            print("Movement detected but no face found.")
            if can_send_notification('movement_no_face'):
                lat, lon = get_location()
                if lat and lon:
                    extra_info = f" Location: lat={lat}, lon={lon}"
                    send_notification(NOTIFICATION_EMAIL, "Movement Detected", f"Movement detected but no face found.{extra_info}", JWT_TOKEN, event_key='movement_no_face')
                else:
                    send_notification(NOTIFICATION_EMAIL, "Movement Detected", "Movement detected but no face found.", JWT_TOKEN, event_key='movement_no_face')

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            encodings = faces_cache['encodings'] if faces_cache['encodings'] else []
            names = faces_cache['names'] if faces_cache['names'] else []
            is_authorized_list = faces_cache['is_authorized'] if 'is_authorized' in faces_cache else []
            if encodings:
                distances = face_recognition.face_distance(encodings, face_encoding)
                best_match_index = np.argmin(distances)
                name = "unknown"
                is_authorized = False
                if distances[best_match_index] < CONFIDENCE_THRESHOLD:
                    name = names[best_match_index]
                    is_authorized = is_authorized_list[best_match_index] if best_match_index < len(is_authorized_list) else False
                    if is_authorized:
                        if can_send_notification(name):
                            lat, lon = get_location()
                            if lat and lon:
                                extra_info = f" Location: lat={lat}, lon={lon}"
                                send_notification(NOTIFICATION_EMAIL, f"Known Face Detected: {name}", f"Detected authorized person {name} in the car.{extra_info}", JWT_TOKEN, event_key=name)
                            else:
                                send_notification(NOTIFICATION_EMAIL, f"Known Face Detected: {name}", f"Detected authorized person {name} in the car.", JWT_TOKEN, event_key=name)
                    else:
                        if can_send_notification(f"unauthorized_{name}"):
                            lat, lon = get_location()
                            if lat and lon:
                                extra_info = f" Location: lat={lat}, lon={lon}"
                                send_notification(NOTIFICATION_EMAIL, f"Unauthorized Access Attempt: {name}", f"This person ({name}) is NOT AUTHORIZED but is trying to access the vehicle.{extra_info}", JWT_TOKEN, event_key=f"unauthorized_{name}")
                            else:
                                send_notification(NOTIFICATION_EMAIL, f"Unauthorized Access Attempt: {name}", f"This person ({name}) is NOT AUTHORIZED but is trying to access the vehicle.", JWT_TOKEN, event_key=f"unauthorized_{name}")
                else:
                    if can_send_notification('unknown'):
                        lat, lon = get_location()
                        if lat and lon:
                            extra_info = f" Location: lat={lat}, lon={lon}"
                            send_notification(NOTIFICATION_EMAIL, "Unknown Face Detected", f"An unknown person was detected in the car.{extra_info}", JWT_TOKEN, event_key='unknown')
                        else:
                            send_notification(NOTIFICATION_EMAIL, "Unknown Face Detected", "An unknown person was detected in the car.", JWT_TOKEN, event_key='unknown')
                print(f"Detected: {name}, Distance: {distances[best_match_index]:.2f}, Authorized: {is_authorized}")
                color = (0, 255, 0) if name != "unknown" and is_authorized else (0, 0, 255)
            else:
                name = "unknown"
                color = (0, 0, 255)
                print("No known faces loaded.")
            # Draw box and label
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        # Always process notification retries in the main loop
        process_notification_retries()

        cv2.imshow('Facial Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
