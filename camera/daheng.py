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
        # Ensure any previous connection is fully closed first
        self.stop()

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
            # Clean up any partially-opened device
            if self._cam is not None:
                try:
                    self._cam.close_device()
                except Exception:
                    pass
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

    # ---- parameter introspection -------------------------------------------

    # Registry of all tuneable parameters.
    # Each entry maps a human-readable key to:
    #   attr       – gxipy device attribute name
    #   auto_attr  – optional auto-mode attribute (None if not applicable)
    #   label      – UI label
    #   unit       – display unit
    #   kind       – "float" | "int" | "bool"
    PARAM_REGISTRY: list[dict] = [
        {"key": "exposure_time",   "attr": "ExposureTime",   "auto_attr": "ExposureAuto",      "label": "Exposure Time",       "unit": "µs",   "kind": "float"},
        {"key": "gain",            "attr": "Gain",            "auto_attr": "GainAuto",           "label": "Gain",                "unit": "dB",   "kind": "float"},
        {"key": "black_level",     "attr": "BlackLevel",      "auto_attr": None,                 "label": "Black Level",         "unit": "",     "kind": "float"},
        {"key": "gamma",           "attr": "Gamma",           "auto_attr": None,                 "label": "Gamma",               "unit": "",     "kind": "float"},
        {"key": "gamma_enable",    "attr": "GammaEnable",     "auto_attr": None,                 "label": "Gamma Enable",        "unit": "",     "kind": "bool"},
        {"key": "sharpness",       "attr": "Sharpness",       "auto_attr": None,                 "label": "Sharpness",           "unit": "",     "kind": "float"},
        {"key": "saturation",      "attr": "Saturation",      "auto_attr": None,                 "label": "Saturation",          "unit": "",     "kind": "int"},
        {"key": "contrast",        "attr": "ContrastParam",   "auto_attr": None,                 "label": "Contrast",            "unit": "",     "kind": "int"},
        {"key": "balance_ratio_r", "attr": "BalanceRatio",     "auto_attr": None,                 "label": "White Balance Red",   "unit": "",     "kind": "float", "selector": ("BalanceRatioSelector", "RED")},
        {"key": "balance_ratio_g", "attr": "BalanceRatio",     "auto_attr": None,                 "label": "White Balance Green", "unit": "",     "kind": "float", "selector": ("BalanceRatioSelector", "GREEN")},
        {"key": "balance_ratio_b", "attr": "BalanceRatio",     "auto_attr": None,                 "label": "White Balance Blue",  "unit": "",     "kind": "float", "selector": ("BalanceRatioSelector", "BLUE")},
        {"key": "auto_white_balance", "attr": "BalanceWhiteAuto", "auto_attr": None,              "label": "Auto White Balance",  "unit": "",     "kind": "enum_auto"},
        {"key": "frame_rate",      "attr": "AcquisitionFrameRate", "auto_attr": None,             "label": "Frame Rate",          "unit": "fps",  "kind": "float"},
    ]

    def get_available_parameters(self) -> list[dict]:
        """Query the camera and return metadata for each supported parameter.

        Returns a list of dicts, each containing:
        - key, label, unit, kind  (from PARAM_REGISTRY)
        - value   – current value
        - min, max, inc  – range (for numeric types)
        - available – True
        """
        if self._cam is None:
            return []

        result = []
        for spec in self.PARAM_REGISTRY:
            try:
                # Select the channel first for white-balance ratio params
                if "selector" in spec:
                    sel_attr, sel_value = spec["selector"]
                    selector = getattr(self._cam, sel_attr, None)
                    if selector is None or not selector.is_implemented():
                        continue
                    # Map string name to enum value
                    sel_range = selector.get_range()
                    matched = [e for e in sel_range if sel_value.upper() in str(e).upper()]
                    if not matched:
                        continue
                    selector.set(matched[0])

                node = getattr(self._cam, spec["attr"], None)
                if node is None or not node.is_implemented():
                    continue

                entry = {
                    "key": spec["key"],
                    "label": spec["label"],
                    "unit": spec["unit"],
                    "kind": spec["kind"],
                    "available": True,
                }

                if spec["kind"] in ("float", "int"):
                    entry["value"] = node.get()
                    r = node.get_range()
                    entry["min"] = r["min"]
                    entry["max"] = r["max"]
                    entry["inc"] = r.get("inc", 1)
                elif spec["kind"] == "bool":
                    entry["value"] = bool(node.get())
                elif spec["kind"] == "enum_auto":
                    cur = node.get()
                    # Normalise to bool (OFF → False, CONTINUOUS/ONCE → True)
                    entry["value"] = (cur != gx.GxAutoEntry.OFF)

                result.append(entry)
            except Exception:
                # Parameter not supported on this model — skip silently
                continue

        return result

    # ---- generic parameter setter ------------------------------------------

    def set_parameter(self, key: str, value) -> bool:
        """Set a camera parameter by its registry key.

        Parameters
        ----------
        key : str
            One of the ``key`` values in :pyattr:`PARAM_REGISTRY`.
        value
            The value to set (type depends on the parameter kind).

        Returns True on success.
        """
        if self._cam is None:
            return False

        spec = next((s for s in self.PARAM_REGISTRY if s["key"] == key), None)
        if spec is None:
            print(f"[DahengCamera] Unknown parameter key: {key}")
            return False

        try:
            # Channel selector (white balance R/G/B)
            if "selector" in spec:
                sel_attr, sel_value = spec["selector"]
                selector = getattr(self._cam, sel_attr, None)
                if selector is None or not selector.is_implemented():
                    return False
                sel_range = selector.get_range()
                matched = [e for e in sel_range if sel_value.upper() in str(e).upper()]
                if not matched:
                    return False
                selector.set(matched[0])

            node = getattr(self._cam, spec["attr"], None)
            if node is None or not node.is_implemented():
                return False

            if spec["kind"] == "float":
                node.set(float(value))
            elif spec["kind"] == "int":
                node.set(int(value))
            elif spec["kind"] == "bool":
                node.set(bool(value))
            elif spec["kind"] == "enum_auto":
                mode = gx.GxAutoEntry.CONTINUOUS if value else gx.GxAutoEntry.OFF
                node.set(mode)

            print(f"[DahengCamera] {spec['label']} set to {value}")
            return True

        except Exception as exc:
            print(f"[DahengCamera] Failed to set {spec['label']}: {exc}")
            return False

    def get_parameter(self, key: str):
        """Read back a single parameter value (or None on failure)."""
        if self._cam is None:
            return None
        spec = next((s for s in self.PARAM_REGISTRY if s["key"] == key), None)
        if spec is None:
            return None
        try:
            if "selector" in spec:
                sel_attr, sel_value = spec["selector"]
                selector = getattr(self._cam, sel_attr, None)
                if selector is None or not selector.is_implemented():
                    return None
                sel_range = selector.get_range()
                matched = [e for e in sel_range if sel_value.upper() in str(e).upper()]
                if not matched:
                    return None
                selector.set(matched[0])

            node = getattr(self._cam, spec["attr"], None)
            if node is None or not node.is_implemented():
                return None

            if spec["kind"] == "enum_auto":
                return node.get() != gx.GxAutoEntry.OFF
            return node.get()
        except Exception:
            return None

    # ---- convenience setters (kept for backward compat) --------------------

    def set_exposure(self, exposure_us: float) -> bool:
        return self.set_parameter("exposure_time", exposure_us)

    def set_gain(self, gain_db: float) -> bool:
        return self.set_parameter("gain", gain_db)

    def set_white_balance(self, auto: bool = True) -> bool:
        return self.set_parameter("auto_white_balance", auto)

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

