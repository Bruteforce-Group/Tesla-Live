from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from .masking import MaskSmoother, MaskingConfig, apply_privacy_masks
from .types import (
    ALERT_CLASSES,
    VEHICLE_CLASSES,
    BBox,
    Detection,
    FaceDetection,
    PlateDetection,
)

# Hailo imports - these will be available when HailoRT is installed
try:
    from hailo_platform import (
        HEF,
        InferVStreams,
        VDevice,
    )

    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False
    print("Warning: Hailo runtime not available, using mock detector")


class HailoDetector:
    """Hailo-8L inference wrapper for object detection."""

    def __init__(self, config):
        self.config = config
        self.device = None
        self.yolo_hef = None
        self.plate_hef = None
        self.mask_config = MaskingConfig(
            inflate_ratio=self.config.mask_inflate_ratio,
            min_size=self.config.mask_min_size,
            mask_type=self.config.mask_type,
            blur_kernel=self.config.mask_blur_kernel,
            mosaic_block=self.config.mask_mosaic_block_size,
            persist_ms=self.config.mask_persist_ms,
            smooth_alpha=self.config.mask_smooth_alpha,
        )
        self.mask_smoother = MaskSmoother(self.mask_config)

        if HAILO_AVAILABLE:
            self._init_hailo()

    def _init_hailo(self):
        """Initialize Hailo device and load models."""
        self.device = VDevice()

        yolo_path = self.config.models_path / "yolov8n.hef"
        if isinstance(yolo_path, Path) and yolo_path.exists():
            self.yolo_hef = HEF(str(yolo_path))

        plate_path = self.config.models_path / "plate_detector.hef"
        if isinstance(plate_path, Path) and plate_path.exists():
            self.plate_hef = HEF(str(plate_path))

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run object detection on frame."""
        if not HAILO_AVAILABLE or self.yolo_hef is None:
            return self._mock_detect(frame)

        input_data = self._preprocess_yolo(frame)

        with self.device.configure(self.yolo_hef) as configured_net:
            input_vstream_info = configured_net.get_input_vstream_infos()[0]
            output_vstream_info = configured_net.get_output_vstream_infos()[0]

            with InferVStreams(
                configured_net, input_vstream_info, output_vstream_info
            ) as infer_pipeline:
                infer_results = infer_pipeline.infer({input_vstream_info.name: input_data})

        detections = self._postprocess_yolo(infer_results, frame.shape)

        enriched: list[Detection] = []
        for det in detections:
            if det.class_name in self.VEHICLE_CLASSES:
                plate_det = self._detect_plate_in_vehicle(frame, det.bbox)
                if plate_det is not None:
                    enriched.append(
                        PlateDetection(
                            class_name=det.class_name,
                            class_id=det.class_id,
                            confidence=det.confidence,
                            bbox=det.bbox,
                            plate_crop=plate_det,
                        )
                    )
                    continue
            enriched.append(det)

        return enriched

    def _preprocess_yolo(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for YOLOv8."""
        resized = cv2.resize(frame, (640, 640))
        normalized = resized.astype(np.float32) / 255.0
        transposed = np.transpose(normalized, (2, 0, 1))
        batched = np.expand_dims(transposed, 0)
        return batched

    def _postprocess_yolo(self, _outputs: dict, _original_shape: tuple) -> list[Detection]:
        """Postprocess YOLOv8 outputs to detections."""
        # TODO: implement decoding + NMS when Hailo outputs are available
        return []

    def _detect_plate_in_vehicle(self, frame: np.ndarray, vehicle_bbox: BBox) -> np.ndarray | None:
        """Detect and crop license plate within vehicle bounding box."""
        if self.plate_hef is None:
            return None

        x1, y1, x2, y2 = (
            int(vehicle_bbox.x1),
            int(vehicle_bbox.y1),
            int(vehicle_bbox.x2),
            int(vehicle_bbox.y2),
        )
        vehicle_crop = frame[y1:y2, x1:x2]

        # TODO: run plate detector inference; return plate crop if found
        _ = vehicle_crop
        return None

    def _mock_detect(self, frame: np.ndarray) -> list[Detection]:
        """Mock detection for testing without Hailo."""
        _ = frame
        return []

    def mask_frame(
        self,
        frame: np.ndarray,
        detections: Iterable[Detection],
        categories_to_mask: Iterable[str] | None = None,
    ) -> tuple[np.ndarray, list[dict]]:
        """
        Apply privacy masking using configured strategy.

        Returns masked frame and mask metadata for downstream logging.
        """
        return apply_privacy_masks(
            frame=frame,
            detections=detections,
            config=self.mask_config,
            smoother=self.mask_smoother,
            categories_to_mask=categories_to_mask,
        )
