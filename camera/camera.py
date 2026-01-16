import cv2
from camera.intel_realsense import IntelRealSenseD435i

class Camera:
    _GUID_DEVINTERFACE_IMAGE = "{e5323777-f976-4f5b-9b55-b94699c46e44}"

    def __init__(self):
        pass

    @staticmethod
    def _build_device_path(device_id: str) -> str:
        sanitized = device_id.replace("\\", "#")
        return f"@device_pnp_\\\\?\\{sanitized}#{Camera._GUID_DEVINTERFACE_IMAGE}"

    def get_cameras_list(self):
        """Get a list of connected camera devices."""
        import win32com.client

        locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        service = locator.ConnectServer(".", "root\\CIMV2")
        devices = service.ExecQuery(
            "SELECT Name, DeviceID FROM Win32_PnPEntity WHERE Service='usbvideo'"
        )

        cameras = []
        for idx, device in enumerate(devices):
            cameras.append(
                {
                    "index": idx,
                    "name": device.Name,
                    "device_path": self._build_device_path(device.DeviceID),
                }
            )
        return cameras

    def load_cap(self, index: int, camera_type: str = "usb-standard"):
        """Load a video capture object for the given camera index."""
        if camera_type == "usb-standard":
            cap = cv2.VideoCapture(index)
            if not cap.isOpened():
                raise ValueError(f"Camera with index {index} could not be opened.")
            return cap
        elif camera_type == "intel-realsense":
            cap = IntelRealSenseD435i()
            if not cap.start():
                raise RuntimeError("Failed to start Intel RealSense camera.")
            return cap
        else:
            raise ValueError(f"Unknown camera type: {camera_type}")

    def read_frame(self, cap):
        """Read a frame from the given video capture object."""
        if isinstance(cap, cv2.VideoCapture):
            return cap.read()
        elif isinstance(cap, IntelRealSenseD435i):
            frame = cap.get_bgr_frame()
            if frame is not None:
                return True, frame
            else:
                return False, None
        else:
            print(f"Unknown capture object type: {type(cap)}")
            return False, None

    def release_cap(self, cap):
        """Release the given video capture object."""
        try:
            if isinstance(cap, cv2.VideoCapture):
                if cap.isOpened():
                    cap.release()
                print("Released USB camera")
            elif isinstance(cap, IntelRealSenseD435i):
                cap.stop()
            else:
                print(f"Unknown capture object type for release: {type(cap)}")
        except Exception as e:
            print(f"Error releasing camera: {e}")


if __name__ == "__main__":
    camera = Camera()
    cameras = camera.get_cameras_list()
    for cam in cameras:
        print(f"Index: {cam['index']}, Name: {cam['name']}, Device Path: {cam['device_path']}")

    # Example to load standard USB camera
    # cap = camera.load_cap(0, camera_type="usb-standard")

    # Example to load Intel RealSense camera
    cap = camera.load_cap(0, camera_type="intel-realsense")

    while True:
        ret, frame = camera.read_frame(cap)
        if not ret:
            break
        cv2.imshow("Camera Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    camera.release_cap(cap)
