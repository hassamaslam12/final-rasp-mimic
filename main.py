import cv2
import numpy as np
import face_recognition
from constants import CONFIDENCE_THRESHOLD

import base64
from notification_utils import send_notification, can_send_notification, process_notification_retries
from faces_api import fetch_faces, faces_cache
import os
from dotenv import load_dotenv

load_dotenv()

NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
JWT_TOKEN = os.getenv('NOTIFICATION_JWT_TOKEN', 'YOUR_JWT_TOKEN_HERE')

def base64_to_nparray(b64_string):
    decoded = base64.b64decode(b64_string)
    arr = np.frombuffer(decoded, dtype=np.float64)
    return arr


def main():
    # Fetch faces once at the start
    fetch_faces()
    video_capture = cv2.VideoCapture(0)
    while not video_capture.isOpened():
        print("Error: Could not open webcam. Retrying in 3 seconds...")
        import time
        time.sleep(3)
        video_capture = cv2.VideoCapture(0)

    print("Starting camera. Press 'q' to quit.")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame. Attempting to restart camera...")
            video_capture.release()
            import time
            time.sleep(2)
            video_capture = cv2.VideoCapture(0)
            continue

        # Check if the frame is black (all pixels are very dark)
        if np.mean(frame) < 10:  # Threshold can be adjusted if needed
            print("Temper alert: camera screen is black")
            if can_send_notification('temper'):
                send_notification(NOTIFICATION_EMAIL, "Temper Alert", "Camera screen is black (possible tampering)", JWT_TOKEN, event_key='temper')
            cv2.imshow('Facial Recognition', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        rgb_frame = frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            encodings = faces_cache['encodings'] if faces_cache['encodings'] else []
            names = faces_cache['names'] if faces_cache['names'] else []
            if encodings:
                distances = face_recognition.face_distance(encodings, face_encoding)
                best_match_index = np.argmin(distances)
                name = "unknown"
                if distances[best_match_index] < CONFIDENCE_THRESHOLD:
                    name = names[best_match_index]
                    if can_send_notification(name):
                        send_notification(NOTIFICATION_EMAIL, f"Known Face Detected: {name}", f"Detected {name} in the car.", JWT_TOKEN, event_key=name)
                else:
                    if can_send_notification('unknown'):
                        send_notification(NOTIFICATION_EMAIL, "Unknown Face Detected", "An unknown person was detected in the car.", JWT_TOKEN, event_key='unknown')
                print(f"Detected: {name}, Distance: {distances[best_match_index]:.2f}")
                color = (0, 255, 0) if name != "unknown" else (0, 0, 255)
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
