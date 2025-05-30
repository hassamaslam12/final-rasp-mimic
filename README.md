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
   - The app will use your default webcam for face recognition.
   - Notifications will be sent on known/unknown/temper events, with retry and interval control.

---

## Prompt to Convert This Code for Raspberry Pi

> Convert this Python OpenCV + face_recognition webcam notification system to run efficiently on a Raspberry Pi (e.g., Pi 4). Ensure compatibility with the Pi camera module, optimize for low resources, and update any package or code sections as needed for ARM architecture and Pi OS. Provide all necessary steps, dependencies, and hardware-specific adjustments required to achieve smooth operation on Raspberry Pi hardware.
