"""Privacy masking utilities aligned to the AI camera strategy."""

from dataclasses import dataclass
from time import monotonic
from typing import Iterable, List, Tuple

import cv2
import numpy as np

from .types import BBox, Detection


@dataclass
class MaskingConfig:
    inflate_ratio: float = 0.4  # 40% box inflation by default
    min_size: int = 32
    mask_type: str = "pixelate"  # or "blur"
    blur_kernel: int = 51
    mosaic_block: int = 12
    persist_ms: int = 500
    smooth_alpha: float = 0.6  # exponential smoothing for jitter


class MaskSmoother:
    """Maintains short-lived mask boxes to reduce flicker and handle brief occlusions."""

    def __init__(self, config: MaskingConfig):
        self.config = config
        self._boxes: list[tuple[BBox, float]] = []

    def update(self, boxes: Iterable[BBox]) -> list[BBox]:
        now = monotonic()
        inflated: list[tuple[BBox, float]] = []

        for box in boxes:
            inflated.append((box, now + self.config.persist_ms / 1000.0))

        # keep existing boxes that have not expired
        kept: list[tuple[BBox, float]] = [
            (box, expiry) for box, expiry in self._boxes if expiry > now
        ]
        all_boxes = kept + inflated
        # smooth coordinates to reduce jitter
        smoothed: list[tuple[BBox, float]] = []
        for box, expiry in all_boxes:
            prev = self._find_previous(box)
            if prev is None:
                smoothed.append((box, expiry))
                continue
            smoothed_box = self._smooth_box(prev, box)
            smoothed.append((smoothed_box, expiry))

        self._boxes = smoothed
        return [box for box, expiry in smoothed if expiry > now]

    def _find_previous(self, target: BBox) -> BBox | None:
        if not self._boxes:
            return None
        # simple nearest-neighbour match
        best_box = None
        best_dist = float("inf")
        for box, _expiry in self._boxes:
            dist = (box.center[0] - target.center[0]) ** 2 + (
                box.center[1] - target.center[1]
            ) ** 2
            if dist < best_dist:
                best_dist = dist
                best_box = box
        return best_box

    def _smooth_box(self, prev: BBox, current: BBox) -> BBox:
        a = self.config.smooth_alpha
        return BBox(
            x1=prev.x1 * a + current.x1 * (1 - a),
            y1=prev.y1 * a + current.y1 * (1 - a),
            x2=prev.x2 * a + current.x2 * (1 - a),
            y2=prev.y2 * a + current.y2 * (1 - a),
        )


def _inflate_bbox(bbox: BBox, frame_shape: Tuple[int, int, int], ratio: float) -> BBox:
    h, w, _ = frame_shape
    dw = bbox.width * ratio
    dh = bbox.height * ratio
    x1 = max(0, bbox.x1 - dw)
    y1 = max(0, bbox.y1 - dh)
    x2 = min(w, bbox.x2 + dw)
    y2 = min(h, bbox.y2 + dh)
    return BBox(x1=x1, y1=y1, x2=x2, y2=y2)


def _clamp_min_size(bbox: BBox, min_size: int, frame_shape: Tuple[int, int, int]) -> BBox:
    h, w, _ = frame_shape
    width = max(bbox.width, min_size)
    height = max(bbox.height, min_size)
    cx, cy = bbox.center
    x1 = max(0, cx - width / 2)
    y1 = max(0, cy - height / 2)
    x2 = min(w, cx + width / 2)
    y2 = min(h, cy + height / 2)
    return BBox(x1=x1, y1=y1, x2=x2, y2=y2)


def _apply_pixelate(frame: np.ndarray, bbox: BBox, block: int) -> None:
    x1, y1, x2, y2 = map(int, (bbox.x1, bbox.y1, bbox.x2, bbox.y2))
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return
    small = cv2.resize(roi, (max(1, (x2 - x1) // block), max(1, (y2 - y1) // block)), interpolation=cv2.INTER_LINEAR)
    pixelated = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)
    frame[y1:y2, x1:x2] = pixelated


def _apply_blur(frame: np.ndarray, bbox: BBox, kernel: int) -> None:
    x1, y1, x2, y2 = map(int, (bbox.x1, bbox.y1, bbox.x2, bbox.y2))
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return
    k = kernel if kernel % 2 == 1 else kernel + 1  # ensure odd kernel for GaussianBlur
    blurred = cv2.GaussianBlur(roi, (k, k), 0)
    frame[y1:y2, x1:x2] = blurred


def apply_privacy_masks(
    frame: np.ndarray,
    detections: Iterable[Detection],
    config: MaskingConfig,
    smoother: MaskSmoother | None = None,
    categories_to_mask: Iterable[str] | None = None,
) -> tuple[np.ndarray, List[dict]]:
    """Apply privacy masks to a frame and return mask metadata."""
    mask_classes = set(categories_to_mask or {"person", "face", "license_plate", "animal"})

    inflated_boxes: list[BBox] = []
    metadata: list[dict] = []
    for det in detections:
        class_name = det.class_name.lower()
        if class_name not in mask_classes:
            continue
        bbox = _inflate_bbox(det.bbox, frame.shape, config.inflate_ratio)
        bbox = _clamp_min_size(bbox, config.min_size, frame.shape)
        inflated_boxes.append(bbox)
        metadata.append(
            {
                "class": class_name,
                "confidence": det.confidence,
                "bbox": {
                    "x1": float(bbox.x1),
                    "y1": float(bbox.y1),
                    "x2": float(bbox.x2),
                    "y2": float(bbox.y2),
                },
            }
        )

    if smoother:
        inflated_boxes = smoother.update(inflated_boxes)

    masked_frame = frame.copy()
    for bbox in inflated_boxes:
        if config.mask_type == "blur":
            _apply_blur(masked_frame, bbox, config.blur_kernel)
        else:
            _apply_pixelate(masked_frame, bbox, config.mosaic_block)

    return masked_frame, metadata
