import cv2
from camera.intel_realsense import IntelRealSenseD435i
from camera.daheng import DahengCamera

class Camera:
    _GUID_DEVINTERFACE_IMAGE = "{e5323777-f976-4f5b-9b55-b94699c46e44}"

    def __init__(self):
        pass

    @staticmethod
    def _build_device_path(device_id: str) -> str:
        sanitized = device_id.replace("\\", "#")
        return f"@device_pnp_\\\\?\\{sanitized}#{Camera._GUID_DEVINTERFACE_IMAGE}"

    def get_cameras_list(self, camera_type: str = "usb-standard"):
        """Get a list of connected camera devices for the given type.

        Returns a list of dicts with at least ``index`` and ``name`` keys.
        """
        if camera_type == "daheng-gige":
            return self._enumerate_daheng()
        elif camera_type == "intel-realsense":
            return self._enumerate_realsense()
        else:
            return self._enumerate_usb()

    # ---- per-type enumeration helpers --------------------------------------

    @staticmethod
    def _enumerate_usb() -> list[dict]:
        """Enumerate USB webcam devices via WMI."""
        try:
            import win32com.client
            locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
            service = locator.ConnectServer(".", "root\\CIMV2")
            devices = service.ExecQuery(
                "SELECT Name, DeviceID FROM Win32_PnPEntity WHERE Service='usbvideo'"
            )
            cameras = []
            for idx, device in enumerate(devices):
                cameras.append({"index": idx, "name": device.Name})
            return cameras
        except Exception as exc:
            print(f"[Camera] USB enumeration error: {exc}")
            return []

    @staticmethod
    def _enumerate_daheng() -> list[dict]:
        """Enumerate Daheng Imaging GigE / USB3 Vision devices."""
        devices = DahengCamera.enumerate_devices()
        cameras = []
        for dev in devices:
            label = f"{dev.get('model', 'Daheng')} (SN: {dev.get('serial', '?')})"
            if dev.get("ip"):
                label += f" [{dev['ip']}]"
            cameras.append({"index": dev["index"] - 1, "name": label})
        return cameras

    @staticmethod
    def _enumerate_realsense() -> list[dict]:
        """Enumerate Intel RealSense devices."""
        try:
            import pyrealsense2 as rs
            ctx = rs.context()
            cameras = []
            for idx, dev in enumerate(ctx.query_devices()):
                name = dev.get_info(rs.camera_info.name)
                serial = dev.get_info(rs.camera_info.serial_number)
                cameras.append({"index": idx, "name": f"{name} (SN: {serial})"})
            return cameras
        except Exception as exc:
            print(f"[Camera] RealSense enumeration error: {exc}")
            return []

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
        elif camera_type == "daheng-gige":
            cap = DahengCamera(device_index=index + 1)  # gxipy uses 1-based
            if not cap.start():
                raise RuntimeError("Failed to start Daheng camera.")
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
        elif isinstance(cap, DahengCamera):
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
            elif isinstance(cap, DahengCamera):
                cap.stop()
            else:
                print(f"Unknown capture object type for release: {type(cap)}")
        except Exception as e:
            print(f"Error releasing camera: {e}")

    def set_autofocus(self, cap, enabled: bool) -> bool:
        """
        Enable or disable camera autofocus.

        Args:
            cap: Camera capture object
            enabled: True to enable autofocus, False to disable

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if isinstance(cap, cv2.VideoCapture):
                if not cap.isOpened():
                    print("Camera is not opened")
                    return False
                # cv2.CAP_PROP_AUTOFOCUS: 1 = enable, 0 = disable
                success = cap.set(cv2.CAP_PROP_AUTOFOCUS, 1 if enabled else 0)
                if success:
                    print(f"Autofocus {'enabled' if enabled else 'disabled'}")
                else:
                    print(f"Warning: Could not set autofocus (camera may not support this feature)")
                return success
            elif isinstance(cap, IntelRealSenseD435i):
                # RealSense cameras handle autofocus through their own API
                success = cap.set_autofocus(enabled)
                if success:
                    print(f"RealSense autofocus {'enabled' if enabled else 'disabled'}")
                return success
            elif isinstance(cap, DahengCamera):
                # Daheng industrial cameras typically don't support autofocus
                print("Daheng camera does not support autofocus")
                return False
            else:
                print(f"Unknown capture object type: {type(cap)}")
                return False
        except Exception as e:
            print(f"Failed to set autofocus: {e}")
            return False

    def set_manual_focus(self, cap, focus_value: int) -> bool:
        """
        Set manual focus value.

        Args:
            cap: Camera capture object
            focus_value: Focus value (0-255, where 0 is near and 255 is far)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if isinstance(cap, cv2.VideoCapture):
                if not cap.isOpened():
                    print("Camera is not opened")
                    return False
                # First disable autofocus for manual control
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                # Set manual focus value
                success = cap.set(cv2.CAP_PROP_FOCUS, focus_value)
                if success:
                    print(f"Manual focus set to: {focus_value}")
                else:
                    print(f"Warning: Could not set manual focus (camera may not support this feature)")
                return success
            elif isinstance(cap, IntelRealSenseD435i):
                # RealSense cameras handle focus through their own API
                success = cap.set_manual_focus(focus_value)
                if success:
                    print(f"RealSense manual focus set to: {focus_value}")
                return success
            elif isinstance(cap, DahengCamera):
                # Daheng industrial cameras typically use fixed-focus lenses
                print("Daheng camera does not support software focus control")
                return False
            else:
                print(f"Unknown capture object type: {type(cap)}")
                return False
        except Exception as e:
            print(f"Failed to set manual focus: {e}")
            return False


if __name__ == "__main__":
    camera = Camera()

    # Enumerate cameras for each type
    for cam_type in ("usb-standard", "intel-realsense", "daheng-gige"):
        print(f"\n--- {cam_type} ---")
        cameras = camera.get_cameras_list(cam_type)
        for cam in cameras:
            print(f"  Index: {cam['index']}, Name: {cam['name']}")

    # Example: open a Daheng GigE camera
    # cap = camera.load_cap(0, camera_type="daheng-gige")
    # while True:
    #     ret, frame = camera.read_frame(cap)
    #     if not ret:
    #         break
    #     cv2.imshow("Camera Feed", frame)
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    # camera.release_cap(cap)
