"""Daheng Imaging GigE camera driver.

Supports Daheng cameras connected via Ethernet / frame grabber using
the Galaxy SDK (gxipy).  Install the Daheng Galaxy SDK and its Python
API before using this module.

Typical pip install:
    pip install gxipy

Or use the ``gxipy`` package bundled with the Galaxy SDK installer.
"""

import numpy as np

try:
    import gxipy as gx
except ImportError:
    gx = None


class DahengCamera:
    """Capture wrapper for Daheng Imaging GigE / USB3 Vision cameras.

    Parameters
    ----------
    device_index : int
        1-based index of the device to open (default ``1``).
    width : int | None
        Desired image width.  ``None`` keeps the sensor default.
    height : int | None
        Desired image height.  ``None`` keeps the sensor default.
    frame_rate : float
        Acquisition frame rate (fps).
    """

    def __init__(
        self,
        device_index: int = 1,
        width: int | None = None,
        height: int | None = None,
        frame_rate: float = 30.0,
    ) -> None:
        if gx is None:
            raise ImportError(
                "gxipy is not installed. Please install the Daheng Galaxy SDK "
                "and its Python API (pip install gxipy)."
            )

        self.device_index = device_index
        self.width = width
        self.height = height
        self.frame_rate = frame_rate

        self._device_manager = gx.DeviceManager()
        self._cam = None
        self.is_running = False

    # ---- lifecycle ---------------------------------------------------------

    def start(self) -> bool:
        """Open the device and start acquisition.

        Returns ``True`` on success, ``False`` otherwise.
        """
        try:
            dev_num, dev_info_list = self._device_manager.update_device_list()
            if dev_num == 0:
                print("[DahengCamera] No Daheng devices found.")
                return False

            if self.device_index < 1 or self.device_index > dev_num:
                print(
                    f"[DahengCamera] Device index {self.device_index} out of "
                    f"range (1..{dev_num})."
                )
                return False

            self._cam = self._device_manager.open_device_by_index(self.device_index)

            # Print device info
            vendor = self._cam.DeviceVendorName.get()
            model = self._cam.DeviceModelName.get()
            serial = self._cam.DeviceSerialNumber.get()
            print(
                f"[DahengCamera] Opened {vendor} {model} (SN: {serial})"
            )

            # ---- configure sensor ------------------------------------------
            # Set pixel format to 8-bit if available
            if self._cam.PixelFormat.is_implemented():
                pixel_formats = self._cam.PixelFormat.get_range()
                # Prefer BayerRG8 or Mono8 for speed; fall back to whatever is available
                for preferred in (gx.GxPixelFormatEntry.BAYER_RG8,
                                  gx.GxPixelFormatEntry.BAYER_GR8,
                                  gx.GxPixelFormatEntry.MONO8):
                    if preferred in pixel_formats:
                        self._cam.PixelFormat.set(preferred)
                        break

            # Resolution
            if self.width and self._cam.Width.is_implemented():
                self._cam.Width.set(self.width)
            if self.height and self._cam.Height.is_implemented():
                self._cam.Height.set(self.height)

            # Frame rate
            if self._cam.AcquisitionFrameRateMode.is_implemented():
                self._cam.AcquisitionFrameRateMode.set(
                    gx.GxSwitchEntry.ON
                )
            if self._cam.AcquisitionFrameRate.is_implemented():
                self._cam.AcquisitionFrameRate.set(self.frame_rate)

            # ---- start stream ----------------------------------------------
            self._cam.stream_on()
            self.is_running = True
            print("[DahengCamera] Acquisition started.")
            return True

        except Exception as exc:
            print(f"[DahengCamera] Failed to start: {exc}")
            self.is_running = False
            self._cam = None
            return False

    def stop(self) -> None:
        """Stop acquisition and close the device."""
        if self._cam is not None:
            try:
                if self.is_running:
                    self._cam.stream_off()
                self._cam.close_device()
                print("[DahengCamera] Device closed.")
            except Exception as exc:
                print(f"[DahengCamera] Error stopping: {exc}")
            finally:
                self._cam = None
                self.is_running = False

    # ---- frame capture -----------------------------------------------------

    def get_bgr_frame(self) -> np.ndarray | None:
        """Grab a single BGR frame.

        Returns
        -------
        numpy.ndarray or None
            BGR image suitable for OpenCV, or ``None`` on failure.
        """
        if not self.is_running or self._cam is None:
            return None

        try:
            raw_image = self._cam.data_stream[0].get_image(timeout=1000)
            if raw_image is None or raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
                return None

            # Convert to RGB numpy array via the Galaxy SDK utility
            numpy_image = raw_image.get_numpy_array()
            if numpy_image is None:
                return None

            # Handle different pixel formats
            pixel_format = raw_image.get_pixel_format()
            if pixel_format == gx.GxPixelFormatEntry.MONO8:
                # Mono → BGR
                import cv2
                bgr = cv2.cvtColor(numpy_image, cv2.COLOR_GRAY2BGR)
                return bgr

            # Bayer patterns → RGB via SDK, then convert to BGR
            rgb_image = raw_image.convert("RGB")
            if rgb_image is None:
                return None
            rgb_array = rgb_image.get_numpy_array()
            if rgb_array is None:
                return None
            # RGB → BGR for OpenCV
            bgr = rgb_array[:, :, ::-1].copy()
            return bgr

        except Exception as exc:
            print(f"[DahengCamera] Frame grab error: {exc}")
            return None

    # ---- camera settings ---------------------------------------------------

    def set_exposure(self, exposure_us: float) -> bool:
        """Set exposure time in microseconds."""
        if self._cam is None:
            return False
        try:
            if self._cam.ExposureTime.is_implemented():
                self._cam.ExposureTime.set(exposure_us)
                print(f"[DahengCamera] Exposure set to {exposure_us} µs")
                return True
        except Exception as exc:
            print(f"[DahengCamera] Failed to set exposure: {exc}")
        return False

    def set_gain(self, gain_db: float) -> bool:
        """Set analog gain in dB."""
        if self._cam is None:
            return False
        try:
            if self._cam.Gain.is_implemented():
                self._cam.Gain.set(gain_db)
                print(f"[DahengCamera] Gain set to {gain_db} dB")
                return True
        except Exception as exc:
            print(f"[DahengCamera] Failed to set gain: {exc}")
        return False

    def set_white_balance(self, auto: bool = True) -> bool:
        """Enable or disable auto white balance."""
        if self._cam is None:
            return False
        try:
            if self._cam.BalanceWhiteAuto.is_implemented():
                mode = (
                    gx.GxAutoEntry.CONTINUOUS if auto
                    else gx.GxAutoEntry.OFF
                )
                self._cam.BalanceWhiteAuto.set(mode)
                print(f"[DahengCamera] Auto white balance {'enabled' if auto else 'disabled'}")
                return True
        except Exception as exc:
            print(f"[DahengCamera] Failed to set white balance: {exc}")
        return False

    # ---- static helpers ----------------------------------------------------

    @staticmethod
    def enumerate_devices() -> list[dict]:
        """Return a list of discovered Daheng devices.

        Each entry is a dict with keys ``index``, ``vendor``, ``model``,
        ``serial``, and ``ip`` (for GigE cameras).
        """
        if gx is None:
            return []

        try:
            mgr = gx.DeviceManager()
            dev_num, dev_info_list = mgr.update_device_list()
            devices = []
            for i, info in enumerate(dev_info_list, start=1):
                devices.append({
                    "index": i,
                    "vendor": info.get("vendor_name", "Daheng"),
                    "model": info.get("model_name", "Unknown"),
                    "serial": info.get("sn", ""),
                    "ip": info.get("ip", ""),
                })
            return devices
        except Exception as exc:
            print(f"[DahengCamera] Enumeration error: {exc}")
            return []

