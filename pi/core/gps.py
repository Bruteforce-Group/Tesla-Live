import threading
import time
from dataclasses import dataclass


@dataclass
class GPSData:
    latitude: float | None = None
    longitude: float | None = None
    speed_kmh: float | None = None
    heading: float | None = None


class GPSManager:
    """Lightweight GPS stub. Replace with gpsd integration on hardware."""

    def __init__(self, config):
        self.config = config
        self.speed: float = 0.0
        self.heading: float = 0.0
        self.location_name: str | None = None
        self.has_fix: bool = False
        self._running = False
        self._thread: threading.Thread | None = None
        self._current = GPSData()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _loop(self):
        """Simulated GPS updates."""
        while self._running:
            time.sleep(1)
            # Keep placeholder values; integrate actual GPSD later
            self.has_fix = False

    def get_current(self) -> GPSData | None:
        return self._current
