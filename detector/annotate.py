"""OpenCV-based frame annotation for detection / segmentation results.

Pure functions — no Qt or model dependency.
"""

from typing import List, Dict, Any
import cv2
import numpy as np

# Distinct colours (BGR) for up to 20 classes, then cycles.
_PALETTE = [
    (0, 255, 0),     # green
    (0, 165, 255),   # orange
    (0, 0, 255),     # red
    (255, 0, 0),     # blue
    (255, 255, 0),   # cyan
    (0, 255, 255),   # yellow
    (255, 0, 255),   # magenta
    (180, 105, 255), # pink
    (0, 128, 0),     # dark green
    (128, 0, 128),   # purple
    (0, 215, 255),   # gold
    (235, 206, 135), # sky blue
    (42, 42, 165),   # brown
    (230, 216, 173), # light blue
    (128, 128, 0),   # teal
    (0, 69, 255),    # orange-red
    (60, 20, 220),   # crimson
    (130, 0, 75),    # indigo
    (19, 69, 139),   # saddle brown
    (211, 0, 148),   # deep pink
]


def _colour_for_class(class_id: int) -> tuple:
    """Return a BGR colour for the given class ID."""
    return _PALETTE[class_id % len(_PALETTE)]


def draw_detections(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
    draw_masks: bool = False,
    mask_alpha: float = 0.4,
    box_thickness: int = 2,
    font_scale: float = 0.55,
    font_thickness: int = 1,
) -> np.ndarray:
    """Draw bounding boxes, labels, and optional masks onto a frame.

    Parameters
    ----------
    frame : np.ndarray
        BGR image (H, W, 3).  A copy is made — the original is not mutated.
    detections : list[dict]
        Each dict must contain ``box`` ([x1,y1,x2,y2]), ``label`` (str),
        ``score`` (float), ``class_id`` (int), and optionally ``mask``
        (H×W bool ndarray).
    draw_masks : bool
        Whether to render segmentation masks as semi-transparent overlays.
    mask_alpha : float
        Opacity of the mask overlay (0 = invisible, 1 = opaque).
    box_thickness : int
        Thickness of bounding-box lines.
    font_scale : float
        Font scale for label text.
    font_thickness : int
        Thickness of label text.

    Returns
    -------
    np.ndarray
        Annotated copy of the frame.
    """
    annotated = frame.copy()

    for det in detections:
        box = det["box"]
        label = det["label"]
        score = det["score"]
        class_id = det.get("class_id", 0)
        mask = det.get("mask")

        colour = _colour_for_class(class_id)
        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])

        # --- mask overlay ---
        if draw_masks and mask is not None:
            mask_bool = mask.astype(bool)
            overlay = annotated.copy()
            overlay[mask_bool] = colour
            cv2.addWeighted(overlay, mask_alpha, annotated, 1 - mask_alpha, 0, annotated)

        # --- bounding box ---
        cv2.rectangle(annotated, (x1, y1), (x2, y2), colour, box_thickness)

        # --- label background + text ---
        text = f"{label} {score:.0%}"
        (tw, th), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
        )
        # Label background rectangle (above the box)
        label_y1 = max(y1 - th - baseline - 6, 0)
        label_y2 = y1
        cv2.rectangle(annotated, (x1, label_y1), (x1 + tw + 8, label_y2), colour, -1)

        # Text
        cv2.putText(
            annotated,
            text,
            (x1 + 4, label_y2 - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (0, 0, 0),  # black text on coloured bg
            font_thickness,
            cv2.LINE_AA,
        )

    return annotated

