import cv2
import os
import time

class DatasetCapture:
    """
    A class to capture images from a webcam and save them into specified
    directories for dataset creation.
    """
    def __init__(self, base_path: str = "samples/dataset_captured"):
        """
        Initializes the DatasetCapture instance.

        Args:
            base_path (str): The base directory where the 'ok' and 'defective'
                             subdirectories will be created.
        """
        self.ok_path = os.path.join(base_path, "ok")
        self.defective_path = os.path.join(base_path, "defective")
        self.cap = None

        # Create directories if they don't exist
        os.makedirs(self.ok_path, exist_ok=True)
        os.makedirs(self.defective_path, exist_ok=True)

    def start_capture(self, camera_index: int = 0):
        """
        Starts the video capture loop from the specified camera.

        - Press '0' to save the image to the 'ok' folder.
        - Press '1' to save the image to the 'defective' folder.
        - Press 'q' to quit.

        Args:
            camera_index (int): The index of the camera to use.
        """
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            return

        print("Starting camera... Press '0' for OK, '1' for Defective, 'q' to quit.")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Can't receive frame (stream end?). Exiting ...")
                break

            # Display the resulting frame
            cv2.imshow('Camera - Press 0 (OK), 1 (Defective), q (Quit)', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('0'):
                self._save_image(frame, self.ok_path)
            elif key == ord('1'):
                self._save_image(frame, self.defective_path)
            elif key == ord('q'):
                break

        # When everything done, release the capture
        self.cap.release()
        cv2.destroyAllWindows()
        print("Capture session ended.")

    def _save_image(self, frame, path: str):
        """
        Saves the given frame to the specified path with a unique filename.
        """
        timestamp = int(time.time() * 1000)
        filename = f"image_{timestamp}.jpg"
        filepath = os.path.join(path, filename)
        cv2.imwrite(filepath, frame)
        print(f"Saved image to: {filepath}")


if __name__ == '__main__':
    # This is an example of how to use the DatasetCapture class.
    # You need to have opencv-python installed: pip install opencv-python
    try:
        capture = DatasetCapture()
        capture.start_capture()
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure you have 'opencv-python' installed.")
