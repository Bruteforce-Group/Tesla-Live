from dataclasses import dataclass
from typing import ClassVar

import numpy as np


@dataclass
class BBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class Detection:
    class_name: str
    class_id: int
    confidence: float
    bbox: BBox


@dataclass
class PlateDetection(Detection):
    plate_crop: np.ndarray | None = None


@dataclass
class FaceDetection(Detection):
    landmarks: np.ndarray | None = None
    embedding: np.ndarray | None = None


# Shared class lists (kept here to avoid circular imports)
YOLO_CLASSES: ClassVar[list[str]] = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
]

VEHICLE_CLASSES: ClassVar[set[str]] = {"car", "truck", "bus", "motorcycle"}
ALERT_CLASSES: ClassVar[set[str]] = {
    "person",
    "bicycle",
    "car",
    "truck",
    "bus",
    "motorcycle",
    "stop sign",
    "traffic light",
}
