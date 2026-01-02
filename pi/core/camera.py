import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import cv2
import numpy as np


@dataclass
class Frame:
    image: np.ndarray
    timestamp: datetime
    frame_number: int


class CameraManager:
    def __init__(self, config):
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_buffer: deque[Frame] = deque(maxlen=300)  # 10 seconds at 30fps
        self.current_frame: Optional[Frame] = None
        self.frame_count = 0
        self.running = False
        self._lock = threading.Lock()
        self._capture_thread: Optional[threading.Thread] = None

    def start(self):
        """Start camera capture in background thread."""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera_resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera_resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, self.config.camera_fps)

        self.running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def stop(self):
        """Stop camera capture."""
        self.running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()

    def _capture_loop(self):
        """Background thread for continuous frame capture."""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_count += 1
                frame_obj = Frame(
                    image=frame,
                    timestamp=datetime.now(),
                    frame_number=self.frame_count,
                )
                with self._lock:
                    self.current_frame = frame_obj
                    self.frame_buffer.append(frame_obj)

    def get_frame(self) -> Optional[Frame]:
        """Get the current frame (thread-safe)."""
        with self._lock:
            return self.current_frame

    def get_buffer_clip(self, seconds_before: float, seconds_after: float) -> list[Frame]:
        """Get frames from buffer for clip creation."""
        with self._lock:
            frames = list(self.frame_buffer)

        if not frames:
            return []

        now = datetime.now()
        start_time = now - timedelta(seconds=seconds_before)
        end_time = now + timedelta(seconds=seconds_after)

        return [f for f in frames if start_time <= f.timestamp <= end_time]
