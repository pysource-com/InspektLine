import cv2

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

    def load_cap(self, index: int):
        """Load a video capture object for the given camera index."""
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            raise ValueError(f"Camera with index {index} could not be opened.")
        return cap



