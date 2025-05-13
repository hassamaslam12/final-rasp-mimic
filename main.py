import cv2
import numpy as np
import face_recognition
from constants import CONFIDENCE_THRESHOLD

import base64
from notification_utils import send_notification, can_send_notification, process_notification_retries
import os
from dotenv import load_dotenv

load_dotenv()

NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')
JWT_TOKEN = os.getenv('NOTIFICATION_JWT_TOKEN', 'YOUR_JWT_TOKEN_HERE')

def base64_to_nparray(b64_string):
    decoded = base64.b64decode(b64_string)
    arr = np.frombuffer(decoded, dtype=np.float64)
    return arr

# Example usage: paste your base64 string below
HASSAM_B64 = "AAAAYG3Iu78AAAAAgnuUPwAAAADS8LQ/AAAAYEfijT8AAADgoA+kvwAAAEDleK+/AAAAABp5aL8AAABg2Oh8vwAAAICzv8U/AAAAgGEosL8AAADAnarMPwAAAGDa/aU/AAAAQGDbxL8AAAAAue+NvwAAAIAoRHM/AAAAQLcruD8AAADgpGrFvwAAAOBr/qq/AAAAYKw3ur8AAADgUSi6vwAAAABtwZK/AAAAYMzefz8AAABg+NSoPwAAAIAVFZc/AAAA4KgAxr8AAAAArpPWvwAAAGCffcG/AAAAAKl+x78AAAAAo0iQPwAAAGDfsb6/AAAAYGlyjz8AAABgVHOUvwAAAECCebq/AAAAgELbmb8AAABgYjqPvwAAAEDJIok/AAAAoFgqoT8AAABgJACwvwAAAMBa8sw/AAAAAIwplz8AAAAA+dK9vwAAAKCaN4E/AAAAYKi9qD8AAACAEePRPwAAAOAYDMc/AAAAAPNuoD8AAADAJDVhPwAAAEBGRpA/AAAAgB3WtT8AAABgkUDOvwAAAMBmlMQ/AAAAwCp1qD8AAAAAr+m6PwAAAGB5FaI/AAAAgE5+wz8AAACAZkPDvwAAAIB1xXc/AAAA4Jgevj8AAADAwBvHvwAAAOByerM/AAAAYKaLoD8AAACATzWkvwAAAMBa7Uq/AAAAYBxBh78AAACAGUDRPwAAAOAcXsI/AAAAAIEuwb8AAADA5Z6jvwAAAGBcrrs/AAAAwJOBwr8AAABAqWehPwAAAAB/DaK/AAAAwKDevL8AAACAW+DBvwAAAKCTVNO/AAAAAJWluz8AAADAednbPwAAAGDYUMQ/AAAAwMW6xr8AAADgWYudPwAAAACb7sK/AAAAAI/5r78AAADAPlaiPwAAAGAA3ac/AAAAwAHIvr8AAADApXmevwAAAGBIj7e/AAAAAHTzmD8AAABg+5C+PwAAAEBd5bE/AAAAQAQUm78AAADAxWzHPwAAAKCGybC/AAAAwARhSr8AAADAr2mdPwAAAOA4k6W/AAAAgBLuxb8AAAAA2AmvvwAAAEBWr6a/AAAAwBpOez8AAABgAHl3PwAAAEBXU72/AAAAAMEEaz8AAADgjje6PwAAAAC+08y/AAAAALpYtz8AAABgcHd5vwAAAMChgLC/AAAAoJvUoD8AAABgKCW8PwAAAODTIcG/AAAAYOXUr78AAADA3yjFPwAAAEBD+9C/AAAAwMHYwz8AAAAAkQDBPwAAAMCrvYo/AAAAAEO0yD8AAADgQxymPwAAAGDgsLc/AAAAQEyDsL8AAADATEuyPwAAAODSOMO/AAAAwCezkD8AAADAgj1xvwAAAADPI6W/AAAAwM89tz8AAADAIwa3Pw=="
HASSAM_ENCODING = base64_to_nparray(HASSAM_B64)

KNOWN_FACE_ENCODINGS = [HASSAM_ENCODING]
KNOWN_FACE_NAMES = ["hassam"]

def main():
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
            distances = face_recognition.face_distance(KNOWN_FACE_ENCODINGS, face_encoding)
            best_match_index = np.argmin(distances)
            name = "unknown"
            if distances[best_match_index] < CONFIDENCE_THRESHOLD:
                name = KNOWN_FACE_NAMES[best_match_index]
                if can_send_notification(name):
                    send_notification(NOTIFICATION_EMAIL, f"Known Face Detected: {name}", f"Detected {name} in the car.", JWT_TOKEN, event_key=name)
            else:
                if can_send_notification('unknown'):
                    send_notification(NOTIFICATION_EMAIL, "Unknown Face Detected", "An unknown person was detected in the car.", JWT_TOKEN, event_key='unknown')
            print(f"Detected: {name}, Distance: {distances[best_match_index]:.2f}")
            # Draw box and label
            color = (0, 255, 0) if name == "hassam" else (0, 0, 255)
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
