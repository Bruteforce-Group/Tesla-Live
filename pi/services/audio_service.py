"""Audio event pipeline scaffold (log-Mel extraction + alert publishing)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - optional dependency
    sd = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class AudioEvent:
    label: str
    confidence: float
    rms: float
    timestamp: float


class AudioService:
    """Edge-friendly audio classifier scaffold; swap _predict with YAMNet/VGGish."""

    def __init__(self, config, alert_service=None):
        self.config = config
        self.alert_service = alert_service
        self.sample_rate = self.config.audio_sample_rate
        self.window_seconds = self.config.audio_window_seconds
        self.min_confidence = self.config.audio_min_confidence
        self.labels = self.config.audio_labels
        self.enabled = bool(self.config.audio_enabled)

    def record_once(self) -> Optional[np.ndarray]:
        """Capture a single audio window if sounddevice is available."""
        if not self.enabled:
            return None
        if sd is None:
            logger.warning("sounddevice not available; audio capture disabled")
            return None
        duration = self.window_seconds
        try:
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            return audio.flatten()
        except Exception as exc:  # pragma: no cover - hardware dependent
            logger.warning("Audio capture failed: %s", exc)
            return None

    def analyze_chunk(self, audio: np.ndarray) -> List[AudioEvent]:
        """Compute log-Mel features and run lightweight heuristic classifier."""
        if audio is None or not audio.size:
            return []

        rms = float(np.sqrt(np.mean(np.square(audio))))
        log_mel = self._log_mel_spectrogram(audio, self.sample_rate)
        predictions = self._predict(log_mel, rms)

        events: list[AudioEvent] = []
        for pred in predictions:
            if pred["confidence"] < self.min_confidence:
                continue
            events.append(
                AudioEvent(
                    label=pred["label"],
                    confidence=pred["confidence"],
                    rms=rms,
                    timestamp=float(pred.get("timestamp", 0.0)),
                )
            )
        return events

    def publish_events(self, events: List[AudioEvent]):
        """Send audio events to the API for correlation."""
        if not self.alert_service or not events:
            return
        for evt in events:
            payload = {
                "type": "audio_event",
                "label": evt.label,
                "confidence": evt.confidence,
                "rms": evt.rms,
                "timestamp": evt.timestamp,
            }
            # fire and forget; caller may await explicitly if desired
            maybe_coro = self.alert_service.send_audio_event(payload)
            if hasattr(maybe_coro, "__await__"):
                # do not block UI thread; callers can await if running in async loop
                pass

    def _log_mel_spectrogram(
        self, audio: np.ndarray, sample_rate: int, n_fft: int = 512, hop: int = 160, n_mels: int = 40
    ) -> np.ndarray:
        """Compute a lightweight log-Mel spectrogram (approximate)."""
        # frame the signal
        window = np.hanning(n_fft)
        frames = []
        for start in range(0, len(audio) - n_fft, hop):
            frame = audio[start : start + n_fft] * window
            spectrum = np.abs(np.fft.rfft(frame)) ** 2
            frames.append(spectrum)
        if not frames:
            return np.empty((0, n_mels))
        spec = np.stack(frames)

        # crude Mel filterbank: linear spacing over FFT bins
        mel_bins = np.linspace(0, spec.shape[1] - 1, n_mels + 1, dtype=int)
        mel_spec = np.zeros((spec.shape[0], n_mels))
        for i in range(n_mels):
            mel_spec[:, i] = spec[:, mel_bins[i] : mel_bins[i + 1]].mean(axis=1)

        mel_spec = np.clip(mel_spec, a_min=1e-9, a_max=None)
        return np.log(mel_spec)

    def _predict(self, log_mel: np.ndarray, rms: float) -> list[dict]:
        """
        Placeholder classifier.

        If RMS energy is high, emit a generic 'loud_event' to surface into alerts.
        Replace with YAMNet/VGGish when model artifacts are available.
        """
        if log_mel.size == 0:
            return []
        # normalize RMS to [0,1] rough range
        confidence = min(0.99, rms * 10)
        if confidence < self.min_confidence:
            return []
        return [{"label": "loud_event", "confidence": confidence, "timestamp": 0.0}]
