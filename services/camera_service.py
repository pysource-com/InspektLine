"""Camera lifecycle management service.

Owns camera hardware interaction: open, read frames, close, settings.
No Qt dependency — uses callbacks for frame delivery.
"""

from typing import Callable, Optional
import threading
import time

from camera.camera import Camera
from services.settings_service import SettingsService


class CameraService:
    """Manages camera capture lifecycle independently of any GUI.

    Usage::

        svc = CameraService(settings)
        svc.open()
        frame = svc.read_frame()   # returns (ok, numpy_array)
        svc.close()

    For continuous capture in a background thread::

        svc.start(on_frame=my_callback)
        ...
        svc.stop()
    """

    def __init__(self, settings: SettingsService):
        self._settings = settings
        self._camera = Camera()
        self._cap = None
        self._lock = threading.Lock()

        # Background capture
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_frame: Optional[Callable] = None
        self._current_frame = None
        self._frame_count: int = 0

    # ---- properties --------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return self._cap is not None

    @property
    def current_frame(self):
        """Most recent frame (numpy array or None)."""
        return self._current_frame

    @property
    def frame_count(self) -> int:
        return self._frame_count

    # ---- lifecycle ---------------------------------------------------------

    def open(self) -> bool:
        """Open the camera using current settings. Returns True on success."""
        cam = self._settings.camera
        try:
            self._cap = self._camera.load_cap(cam.camera_index, cam.camera_type)
            # Apply initial focus settings
            if self._cap is not None:
                self._camera.set_autofocus(self._cap, cam.auto_focus_enabled)
                if not cam.auto_focus_enabled:
                    self._camera.set_manual_focus(self._cap, cam.manual_focus_value)
            return True
        except Exception as exc:
            print(f"[CameraService] Failed to open camera: {exc}")
            self._cap = None
            return False

    def close(self) -> None:
        """Release camera resources."""
        with self._lock:
            if self._cap is not None:
                try:
                    self._camera.release_cap(self._cap)
                except Exception as exc:
                    print(f"[CameraService] Error releasing camera: {exc}")
                finally:
                    self._cap = None
                    self._current_frame = None

    def reopen(self) -> bool:
        """Close then re-open (e.g. after changing camera device)."""
        self.close()
        time.sleep(0.5)  # allow hardware to fully release
        return self.open()

    # ---- frame reading -----------------------------------------------------

    def read_frame(self):
        """Read a single frame. Returns (success: bool, frame: ndarray|None)."""
        with self._lock:
            if self._cap is None:
                return False, None
            ok, frame = self._camera.read_frame(self._cap)
            if ok:
                self._current_frame = frame.copy()
                self._frame_count += 1
            return ok, frame

    # ---- background capture ------------------------------------------------

    def start(self, on_frame: Callable = None, fps: int = 33) -> None:
        """Start continuous capture on a background thread.

        *on_frame(frame)* is called from the background thread whenever a
        new frame is available.  The GUI should use a signal/slot or
        ``QMetaObject.invokeMethod`` to marshal the call back to the main
        thread.
        """
        if self._running:
            return
        if not self.is_open:
            if not self.open():
                return
        self._on_frame = on_frame
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop, args=(fps,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background capture thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _capture_loop(self, fps: int) -> None:
        interval = 1.0 / fps
        while self._running:
            ok, frame = self.read_frame()
            if ok and self._on_frame is not None:
                try:
                    self._on_frame(frame)
                except Exception as exc:
                    print(f"[CameraService] Frame callback error: {exc}")
            time.sleep(interval)

    # ---- camera hardware settings ------------------------------------------

    def set_autofocus(self, enabled: bool) -> bool:
        """Enable or disable autofocus on the current capture."""
        self._settings.camera.auto_focus_enabled = enabled
        if self._cap is not None:
            return self._camera.set_autofocus(self._cap, enabled)
        return False

    def set_manual_focus(self, value: int) -> bool:
        """Set manual focus value (0-255)."""
        self._settings.camera.manual_focus_value = value
        if self._cap is not None:
            return self._camera.set_manual_focus(self._cap, value)
        return False

    def get_cameras_list(self) -> list:
        """Enumerate available cameras (delegates to Camera)."""
        try:
            return self._camera.get_cameras_list()
        except Exception as exc:
            print(f"[CameraService] Could not enumerate cameras: {exc}")
            return []

