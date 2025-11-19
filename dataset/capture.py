import cv2
import os
from pathlib import Path
from datetime import datetime
from camera import Camera
from config import *

class DatasetCapture:
    def __init__(self, output_dir: str = "../samples/dataset_captured"):
        """
        Initialize the DatasetCapture.

        Args:
            output_dir: Base directory for saving captured images
        """
        self.output_dir = Path(output_dir)
        self.ok_dir = self.output_dir / "ok"
        self.defective_dir = self.output_dir / "defective"

        # Create directories if they don't exist
        self.ok_dir.mkdir(parents=True, exist_ok=True)
        self.defective_dir.mkdir(parents=True, exist_ok=True)

        self.camera = Camera()
        self.ok_count = 0
        self.defective_count = 0

    def _save_image(self, frame, category: str):
        """Save the captured frame to the appropriate directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        if category == "ok":
            filepath = self.ok_dir / f"ok_{timestamp}.jpg"
            self.ok_count += 1
            print(f"Saved OK image: {filepath} (Total: {self.ok_count})")
        elif category == "defective":
            filepath = self.defective_dir / f"defective_{timestamp}.jpg"
            self.defective_count += 1
            print(f"Saved DEFECTIVE image: {filepath} (Total: {self.defective_count})")

        cv2.imwrite(str(filepath), frame)

    def start_capture(self):
        """Start the capture loop."""
        print("Dataset Capture Started")
        print("Press '0' to save as OK")
        print("Press '1' to save as DEFECTIVE")
        print("Press 'q' to quit")

        # load cap
        cap = self.camera.load_cap(CAMERA_INDEX)

        while True:
            frame = self.camera.read_frame(cap)

            if frame is None:
                print("Failed to capture frame")
                break

            # Display the frame
            cv2.imshow("Dataset Capture", frame)

            # Wait for key press
            key = cv2.waitKey(1) & 0xFF

            if key == ord('0'):
                self._save_image(frame, "ok")
            elif key == ord('1'):
                self._save_image(frame, "defective")
            elif key == ord('q'):
                print("Quitting...")
                break

        self.stop()

    def stop(self):
        """Clean up resources."""
        self.camera.release()
        cv2.destroyAllWindows()
        print(f"Capture session ended. OK: {self.ok_count}, Defective: {self.defective_count}")


if __name__ == "__main__":
    capture = DatasetCapture()
    capture.start_capture()
