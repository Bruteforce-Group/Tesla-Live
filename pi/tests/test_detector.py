from core.detector import HailoDetector
from core.config import settings


def test_detector_mock():
    detector = HailoDetector(settings)
    results = detector.detect(None)  # type: ignore[arg-type]
    assert isinstance(results, list)
