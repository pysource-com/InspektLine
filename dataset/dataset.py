import cv2
import os
from datetime import datetime
from camera import Camera
from config import *

save_id = 0  # simple incremental id

camera = Camera()
cap = camera.load_cap(CAMERA_INDEX)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Camera Feed", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q') or key == 27:  # 'q' or ESC to quit
        break

    # key 0 -> images/ok, key 1 -> images/defective
    elif key in (ord('0'), ord('1')):
        label = "ok" if key == ord('0') else "defective"
        folder = os.path.join("images", label)
        os.makedirs(folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_id{save_id:04d}.jpg"
        save_path = os.path.join(folder, filename)

        cv2.imwrite(save_path, frame)
        save_id += 1
