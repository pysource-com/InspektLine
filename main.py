from camera import Camera
import cv2
from config import *

camera = Camera()
cap = camera.load_cap(CAMERA_INDEX)  # Example to load camera with index 2

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Camera Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break