# final-rasp-mimic

## How to Run This Code

1. **Clone the repository:**
   ```sh
   git clone https://github.com/hassamaslam12/final-rasp-mimic.git
   cd final-rasp-mimic
   ```

2. **Set up a Python virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Edit the `.env` file and set:
     - `NOTIFICATION_API_BASEURL` (your notification API base URL)
     - `NOTIFICATION_EMAIL` (user email)
     - `NOTIFICATION_JWT_TOKEN` (your JWT token)
     - `NOTIFICATION_INTERVAL_MINUTES` (notification interval, e.g., 15)

5. **Run the application:**
   ```sh
   python main.py
   ```

6. **Camera & Notifications:**
   - The app will use your default webcam or Pi Camera for face recognition.
   - Notifications will be sent on known/unknown/temper events, with retry and interval control.

---

# Raspberry Pi Setup Guide

## 1. Hardware Requirements
- Raspberry Pi 4 (recommended) or Pi 3B+
- Raspberry Pi Camera Module (or compatible USB webcam)
- MicroSD card with Raspberry Pi OS (Bullseye or newer recommended)
- Internet connection (for notifications and API access)

## 2. System Package Prerequisites
Before installing Python dependencies, install system libraries required for OpenCV, dlib, and camera support:

```sh
sudo apt update
sudo apt upgrade
# Core build tools and libraries
sudo apt install -y build-essential cmake pkg-config libatlas-base-dev libjasper-dev libqtgui4 libqt4-test libilmbase-dev libopenexr-dev libgstreamer1.0-dev libavcodec-dev libavformat-dev libswscale-dev libqt5gui5 libqt5webkit5 libqt5test5 libqt5core5a libqt5network5 libtiff5 libjpeg-dev libpng-dev libavutil-dev libavfilter-dev libavdevice-dev libx264-dev libx265-dev libwebp-dev libdc1394-22-dev libv4l-dev libopenblas-dev liblapack-dev libhdf5-dev libprotobuf-dev protobuf-compiler libgtk2.0-dev libavresample-dev python3-pip python3-venv
# For Pi Camera support (Bullseye+):
sudo apt install -y python3-libcamera python3-kms++ python3-picamera2
```

## 3. Python Environment Setup
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Special Notes for dlib/face_recognition
- On ARM (Raspberry Pi), `dlib` and `face_recognition` may fail to build from source. Use pre-built wheels if available:
  - Find wheels at: https://www.piwheels.org/project/dlib/ and https://www.piwheels.org/project/face-recognition/
  - Install with:
    ```sh
    pip install dlib --extra-index-url https://www.piwheels.org/simple
    pip install face-recognition --extra-index-url https://www.piwheels.org/simple
    ```
- If you encounter build errors, ensure all system dependencies above are installed.
- Use Python 3.7–3.9 for best compatibility.

## 4. Camera Configuration
- For Pi Camera Module (Bullseye+):
  - Enable camera in `raspi-config` (may be optional in modern Pi OS):
    ```sh
    sudo raspi-config
    # Interface Options -> Camera -> Enable
    ```
  - The app will automatically try USB webcam first (OpenCV), then Pi Camera (picamera2). If both fail, it will retry indefinitely.
- For USB webcam, no extra configuration is needed.

## 5. Running the App
```sh
python main.py
```
- The camera will run continuously. If the camera disconnects or fails, the app will automatically attempt to reconnect or switch between USB and Pi Camera.
- All notifications and face recognition features work the same as on desktop.

## 6. Troubleshooting
- **dlib/face_recognition install errors:**
  - Use pre-built wheels from piwheels (see above).
  - Ensure all `apt` dependencies are installed.
- **Camera not detected:**
  - Check camera connection and enablement in `raspi-config`.
  - Try both USB and Pi Camera.
  - Ensure you are running on Raspberry Pi OS Bullseye or newer for `picamera2` support.
- **Performance:**
  - Lower camera resolution in code if needed (default is 640x480).
  - Run face detection on every Nth frame for faster performance (see `main.py`).

---

# About Camera Fallback Logic
- The app will first attempt to use a USB webcam via OpenCV.
- If not available, it will attempt to use the Pi Camera via `picamera2`.
- If both fail, it will retry every 5 seconds until a camera is available.
- If the camera disconnects during operation, it will switch to the other camera type or retry as needed.
- This ensures the camera is running all the time with no manual intervention required.

---

## Prompt to Convert This Code for Raspberry Pi

> Convert this Python OpenCV + face_recognition webcam notification system to run efficiently on a Raspberry Pi (e.g., Pi 4). Ensure compatibility with the Pi camera module, optimize for low resources, and update any package or code sections as needed for ARM architecture and Pi OS. Provide all necessary steps, dependencies, and hardware-specific adjustments required to achieve smooth operation on Raspberry Pi hardware.
