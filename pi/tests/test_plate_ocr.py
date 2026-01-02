import numpy as np

from core.config import settings
from core.plate_ocr import PlateOCR


def test_plate_ocr_handles_empty():
    ocr = PlateOCR(settings)
    assert ocr.recognize(np.array([])) is None
