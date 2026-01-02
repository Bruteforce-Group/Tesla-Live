from core.config import settings
from core.detector import HailoDetector


def test_detector_mock():
    detector = HailoDetector(settings)
    results = detector.detect(None)  # type: ignore[arg-type]
    assert isinstance(results, list)
