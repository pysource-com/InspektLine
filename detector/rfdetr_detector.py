"""RF-DETR object detection and instance segmentation wrapper.

Loads a fine-tuned RF-DETR checkpoint (.pth) and exposes a simple
predict() interface that returns raw numpy arrays — no supervision
dependency in the public API.
"""

import os
from typing import List, Dict, Any, Optional

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Compatibility patch: albucore ≤ 0.0.23 ships MAX_VALUES_BY_DTYPE with only
# np.uint8 / np.float32 entries.  albumentations 1.4.x accesses np.uint32,
# np.uint16, np.float64, np.int32 — which raises KeyError on numpy ≥ 2.0
# where dtype types hash differently.  Patch once at import time.
# ---------------------------------------------------------------------------
try:
    from albucore.utils import MAX_VALUES_BY_DTYPE as _MV

    _EXTRA_DTYPES = {
        np.uint16: 65535,
        np.uint32: 4294967295,
        np.int32: 2147483647,
        np.float64: 1.0,
    }
    for _dt, _val in _EXTRA_DTYPES.items():
        if _dt not in _MV:
            _MV[_dt] = _val
except Exception:
    pass


class RFDETRDetector:
    """Wrapper around the ``rfdetr`` package for object detection / segmentation.

    Parameters
    ----------
    checkpoint_path : str
        Path to a fine-tuned ``.pth`` checkpoint file.
    class_names : list[str] | None
        Human-readable class names, indexed by class ID.
        If *None*, labels will be ``"class_0"``, ``"class_1"``, …
    num_classes : int
        Number of classes the checkpoint was trained on.
    model_variant : str
        Full model variant name, e.g. ``"RF-DETR Base"``, ``"RF-DETRSeg Large"``.
        See :data:`MODEL_REGISTRY` for supported values.
    resolution : int | None
        Input resolution override.  When *None* (default) the model's
        own default resolution is used — this is the safest option.
    device : str | None
        ``"cuda"`` / ``"cpu"`` / *None* (auto-select).
    """

    # Maps display name → rfdetr class name
    MODEL_REGISTRY = {
        # Detection models
        "RF-DETR Nano":         "RFDETRNano",
        "RF-DETR Small":        "RFDETRSmall",
        "RF-DETR Medium":       "RFDETRMedium",
        "RF-DETR Base":         "RFDETRBase",
        "RF-DETR Large":        "RFDETRLarge",
        # Segmentation models
        "RF-DETRSeg Nano":      "RFDETRSegNano",
        "RF-DETRSeg Small":     "RFDETRSegSmall",
        "RF-DETRSeg Medium":    "RFDETRSegMedium",
        "RF-DETRSeg Large":     "RFDETRSegLarge",
        "RF-DETRSeg XLarge":    "RFDETRSegXLarge",
        "RF-DETRSeg 2XLarge":   "RFDETRSeg2XLarge",
    }

    # Each variant's native default resolution (queried from rfdetr configs).
    DEFAULT_RESOLUTION = {
        "RF-DETR Nano":       384,
        "RF-DETR Small":      512,
        "RF-DETR Medium":     576,
        "RF-DETR Base":       560,
        "RF-DETR Large":      704,
        "RF-DETRSeg Nano":    312,
        "RF-DETRSeg Small":   384,
        "RF-DETRSeg Medium":  432,
        "RF-DETRSeg Large":   504,
        "RF-DETRSeg XLarge":  624,
        "RF-DETRSeg 2XLarge": 768,
    }

    DETECTION_MODELS = [
        "RF-DETR Nano", "RF-DETR Small", "RF-DETR Medium",
        "RF-DETR Base", "RF-DETR Large",
    ]

    SEGMENTATION_MODELS = [
        "RF-DETRSeg Nano", "RF-DETRSeg Small", "RF-DETRSeg Medium",
        "RF-DETRSeg Large", "RF-DETRSeg XLarge", "RF-DETRSeg 2XLarge",
    ]

    def __init__(
        self,
        checkpoint_path: str,
        class_names: Optional[List[str]] = None,
        num_classes: int = 1,
        model_variant: str = "RF-DETR Base",
        resolution: Optional[int] = None,
        device: Optional[str] = None,
    ) -> None:
        if not os.path.isfile(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names = class_names
        self.num_classes = num_classes
        self.model_variant = model_variant

        # Resolve the rfdetr class from the variant name
        cls_name = self.MODEL_REGISTRY.get(model_variant)
        if cls_name is None:
            raise ValueError(
                f"Unknown model variant '{model_variant}'. "
                f"Choose from: {list(self.MODEL_REGISTRY.keys())}"
            )

        import rfdetr
        ModelCls = getattr(rfdetr, cls_name)

        # Build kwargs — only override resolution when the caller
        # explicitly provides one (otherwise the model picks its own).
        model_kwargs = dict(
            pretrain_weights=checkpoint_path,
            num_classes=num_classes,
        )
        if resolution is not None:
            model_kwargs["resolution"] = resolution

        self._model = ModelCls(**model_kwargs)
        self._model.optimize_for_inference()
        self.resolution = self._model.model_config.resolution

        # Build default class name map if not provided
        if self.class_names is None:
            self.class_names = [f"class_{i}" for i in range(num_classes)]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @torch.inference_mode()
    def predict(
        self,
        frame: np.ndarray,
        confidence_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Run inference on a single BGR frame.

        Returns
        -------
        list[dict]
            Each dict contains:
            - ``box``   : ``[x1, y1, x2, y2]`` (pixel coords, float)
            - ``label`` : ``str``
            - ``score`` : ``float``
            - ``class_id`` : ``int``
            - ``mask``  : ``np.ndarray | None`` (H×W bool array, if available)
        """
        from PIL import Image
        import cv2

        # RF-DETR expects a PIL RGB image
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        # supervision.Detections returned by rfdetr
        sv_detections = self._model.predict(pil_img, threshold=confidence_threshold)

        detections: List[Dict[str, Any]] = []

        if sv_detections is None or len(sv_detections) == 0:
            return detections

        boxes = sv_detections.xyxy                # (N, 4) float
        scores = sv_detections.confidence         # (N,)   float
        class_ids = sv_detections.class_id        # (N,)   int
        masks = getattr(sv_detections, "mask", None)  # (N, H, W) bool or None

        for i in range(len(boxes)):
            cid = int(class_ids[i])
            label = (
                self.class_names[cid]
                if cid < len(self.class_names)
                else f"class_{cid}"
            )
            det: Dict[str, Any] = {
                "box": boxes[i].tolist(),       # [x1, y1, x2, y2]
                "label": label,
                "score": float(scores[i]),
                "class_id": cid,
                "mask": masks[i] if masks is not None else None,
            }
            detections.append(det)

        return detections

