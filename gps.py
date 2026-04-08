import cv2
import numpy as np
import pyttsx3
import time
import threading
import webbrowser

# =============================
# Text-to-Speech (Non-blocking)
# =============================
engine = pyttsx3.init()
engine.setProperty("rate", 150)

def speak(text):
    def run():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run, daemon=True).start()

# =============================
# Google Maps Setup (NO GPS)
# =============================
SOURCE = "current+location"   # browser uses phone/laptop location
DESTINATION = "nearest bus stop"   # 🔴 change destination here

def open_google_maps():
    url = f"https://www.google.com/maps/dir/{SOURCE}/{DESTINATION}"
    webbrowser.open(url)

# =============================
# CAMERA INITIALIZATION
# =============================
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("ERROR: Camera not accessible")
    exit()

speak("Path guidance system with Google Maps started")
open_google_maps()

# =============================
# PARAMETERS
# =============================
COOLDOWN = 2
last_spoken = 0
frame_count = 0

# =============================
# MAIN LOOP
# =============================
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame_count += 1
    if frame_count % 2 != 0:
        continue

    h, w, _ = frame.shape

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    # Panorama (5 regions)
    step = w // 5
    regions = [
        edges[:, 0:step],
        edges[:, step:2*step],
        edges[:, 2*step:3*step],
        edges[:, 3*step:4*step],
        edges[:, 4*step:w]
    ]

    densities = [np.sum(r) / r.size for r in regions]
    d_fl, d_l, d_c, d_r, d_fr = densities

    direction = "Move Forward"
    if d_c > max(d_l, d_r):
        direction = "Move Left" if d_l < d_r else "Move Right"
    elif d_l > max(d_fl, d_c):
        direction = "Move Right"
    elif d_r > max(d_fr, d_c):
        direction = "Move Left"

    # Voice guidance
    now = time.time()
    if now - last_spoken > COOLDOWN:
        speak(direction)
        last_spoken = now

    # Draw guide lines
    for i in range(1, 5):
        cv2.line(frame, (i * step, 0), (i * step, h), (0, 255, 0), 2)

    cv2.putText(frame, direction, (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("Path Guidance + Google Maps", frame)

    # Press Q to quit, M to reopen Maps
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('m'):
        open_google_maps()
        speak("Google Maps opened")

# =============================
# CLEANUP
# =============================
cap.release()
cv2.destroyAllWindows()

