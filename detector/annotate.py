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
        classification = det.get("classification")  # two-stage result

        colour = _colour_for_class(class_id)

        # Override colour when a classification result exists
        if classification is not None:
            cls_label = classification["label"].lower()
            # Heuristic: labels containing common "bad" keywords → red,
            # otherwise → green.  Covers "defect", "defective", "bad",
            # "ng", "fail", "reject", etc.
            _bad_keywords = {"defect", "defective", "bad", "ng", "fail",
                             "reject", "rejected", "nok", "damaged", "faulty"}
            if cls_label in _bad_keywords or any(k in cls_label for k in _bad_keywords):
                colour = (0, 0, 255)   # red (BGR)
            else:
                colour = (0, 200, 0)   # green (BGR)

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
        tracker_id = det.get("tracker_id")
        if tracker_id is not None and tracker_id >= 0:
            text = f"{label} #{tracker_id} {score:.0%}"
        else:
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

        # --- classification badge (below the bounding box) ---
        if classification is not None:
            cls_text = f"{classification['label']} {classification['score']:.0%}"
            (ctw, cth), c_baseline = cv2.getTextSize(
                cls_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
            )
            cls_y1 = y2
            cls_y2 = min(y2 + cth + c_baseline + 6, annotated.shape[0])
            cv2.rectangle(
                annotated, (x1, cls_y1), (x1 + ctw + 8, cls_y2), colour, -1
            )
            cv2.putText(
                annotated,
                cls_text,
                (x1 + 4, cls_y2 - c_baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),  # white text on coloured bg
                font_thickness,
                cv2.LINE_AA,
            )

    return annotated


def draw_roi_polygon(
    frame: np.ndarray,
    polygon: np.ndarray,
    zone_count: int = 0,
    total_entered: int = 0,
    line_colour: tuple = (0, 255, 255),
    fill_alpha: float = 0.15,
    thickness: int = 2,
) -> np.ndarray:
    """Draw a polygon ROI zone with counters onto a frame.

    Parameters
    ----------
    frame : np.ndarray
        BGR image (H, W, 3).  Modified **in-place** for performance
        (caller typically already has a copy from ``draw_detections``).
    polygon : np.ndarray
        Vertices as an (N, 2) int array.
    zone_count : int
        Objects currently inside the zone.
    total_entered : int
        Total unique objects that have entered the zone.
    line_colour : tuple
        BGR colour for the polygon outline.
    fill_alpha : float
        Opacity of the zone fill.
    thickness : int
        Line thickness for the polygon border.

    Returns
    -------
    np.ndarray
        The frame with the polygon overlay drawn.
    """
    pts = polygon.reshape((-1, 1, 2))

    # Semi-transparent fill
    overlay = frame.copy()
    cv2.fillPoly(overlay, [polygon], line_colour)
    cv2.addWeighted(overlay, fill_alpha, frame, 1 - fill_alpha, 0, frame)

    # Polygon outline
    cv2.polylines(frame, [pts], isClosed=True, color=line_colour, thickness=thickness)

    # Counter badge — top-left corner of the polygon bounding box
    x_min, y_min = polygon.min(axis=0)
    badge_text = f"In zone: {zone_count}  |  Total: {total_entered}"
    (tw, th), baseline = cv2.getTextSize(
        badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
    )
    badge_y = max(y_min - 10, th + 6)
    badge_x = max(x_min, 0)

    cv2.rectangle(
        frame,
        (badge_x, badge_y - th - 6),
        (badge_x + tw + 12, badge_y + 4),
        (0, 0, 0),
        -1,
    )
    cv2.putText(
        frame,
        badge_text,
        (badge_x + 6, badge_y - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        line_colour,
        2,
        cv2.LINE_AA,
    )

    return frame


