import re
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

try:
    from hailo_platform import HEF

    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False
    print("Warning: Hailo runtime not available, plate OCR mock active")


@dataclass
class PlateResult:
    text: str
    confidence: float
    state: Optional[str] = None  # Detected Australian state


class PlateOCR:
    """On-device license plate OCR using LPRNet on Hailo."""

    AU_PLATE_PATTERNS = {
        "QLD": r"^[0-9]{3}[A-Z]{3}$|^[A-Z]{3}[0-9]{3}$",
        "NSW": r"^[A-Z]{2}[0-9]{2}[A-Z]{2}$|^[A-Z]{3}[0-9]{2}[A-Z]$",
        "VIC": r"^[A-Z]{3}[0-9]{3}$|^[0-9]{3}[A-Z]{3}$",
        "SA": r"^[A-Z]{3}[0-9]{3}$|^S[0-9]{3}[A-Z]{3}$",
        "WA": r"^[0-9][A-Z]{3}[0-9]{3}$",
        "TAS": r"^[A-Z]{1,2}[0-9]{4}$",
        "NT": r"^[A-Z]{2}[0-9]{2}[A-Z]{2}$",
        "ACT": r"^[A-Z]{3}[0-9]{2}[A-Z]$|^Y[A-Z]{2}[0-9]{2}[A-Z]$",
    }

    CHAR_SET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, config):
        self.config = config
        self.lprnet_hef = None
        self._load_model()

    def _load_model(self):
        """Load LPRNet model for Hailo."""
        model_path = self.config.models_path / "lprnet.hef"
        if model_path.exists() and HAILO_AVAILABLE:
            self.lprnet_hef = HEF(str(model_path))

    def recognize(self, plate_crop: np.ndarray) -> Optional[PlateResult]:
        """Recognize text from plate crop."""
        if plate_crop is None or plate_crop.size == 0:
            return None

        input_data = self._preprocess(plate_crop)

        if self.lprnet_hef and HAILO_AVAILABLE:
            text, confidence = self._run_inference(input_data)
        else:
            return None

        text = self._clean_text(text)
        state = self._detect_state(text)

        if len(text) < 4:
            return None

        return PlateResult(text=text, confidence=confidence, state=state)

    def _preprocess(self, plate_crop: np.ndarray) -> np.ndarray:
        """Preprocess plate image for LPRNet."""
        resized = cv2.resize(plate_crop, (94, 24))
        if len(resized.shape) == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = resized
        normalized = gray.astype(np.float32) / 255.0
        return np.expand_dims(np.expand_dims(normalized, 0), 0)

    def _run_inference(self, input_data: np.ndarray) -> tuple[str, float]:
        """Run LPRNet inference."""
        # TODO: implement once Hailo model outputs defined
        _ = input_data
        return "", 0.0

    def _clean_text(self, text: str) -> str:
        """Clean and normalize recognized text."""
        cleaned = "".join(c for c in text.upper() if c in self.CHAR_SET)
        corrections = {"0": "O", "O": "0", "1": "I", "I": "1", "8": "B", "B": "8"}
        # TODO: context-aware corrections based on character positions
        _ = corrections
        return cleaned

    def _detect_state(self, text: str) -> Optional[str]:
        """Detect Australian state from plate format."""
        for state, pattern in self.AU_PLATE_PATTERNS.items():
            if re.match(pattern, text):
                return state
        return None
