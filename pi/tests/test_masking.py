import numpy as np

from core.types import BBox, Detection
from core.masking import MaskSmoother, MaskingConfig, apply_privacy_masks


def test_masking_inflates_and_masks_region():
    frame = np.random.randint(0, 255, size=(120, 120, 3), dtype=np.uint8)
    det = Detection(
        class_name="person",
        class_id=0,
        confidence=0.95,
        bbox=BBox(40, 40, 60, 60),
    )
    config = MaskingConfig(
        inflate_ratio=0.5,
        min_size=20,
        mask_type="pixelate",
        mosaic_block=6,
        persist_ms=10,
    )
    smoother = MaskSmoother(config)

    masked, metadata = apply_privacy_masks(
        frame=frame, detections=[det], config=config, smoother=smoother
    )

    assert metadata, "Mask metadata should be emitted"
    inflated_bbox = metadata[0]["bbox"]
    assert inflated_bbox["x1"] < 40 and inflated_bbox["y1"] < 40
    assert inflated_bbox["x2"] > 60 and inflated_bbox["y2"] > 60

    # Region inside the inflated bbox should be altered by pixelation
    bb = metadata[0]["bbox"]
    x1, y1, x2, y2 = map(int, (bb["x1"], bb["y1"], bb["x2"], bb["y2"]))
    orig_region = frame[y1:y2, x1:x2].copy()
    masked_region = masked[y1:y2, x1:x2]
    assert orig_region.shape == masked_region.shape
    assert np.any(orig_region != masked_region)
