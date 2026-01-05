import json
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from .types import BBox

try:
    from hailo_platform import HEF

    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False
    print("Warning: Hailo runtime not available, face recognition mock active")


@dataclass
class FaceMatch:
    face_id: str
    name: str
    confidence: float


@dataclass
class FaceResult:
    bbox: BBox
    confidence: float
    landmarks: np.ndarray
    embedding: np.ndarray
    match: FaceMatch | None = None


class FaceRecognitionPipeline:
    """On-device face detection and recognition using Hailo."""

    def __init__(self, config):
        self.config = config
        self.retinaface_hef = None
        self.arcface_hef = None
        self.enrolled_faces: dict[str, dict] = {}

        self._load_models()
        self._load_enrolled_faces()

    def _load_models(self):
        """Load face detection and embedding models."""
        retinaface_path = self.config.models_path / "retinaface.hef"
        arcface_path = self.config.models_path / "arcface.hef"

        if HAILO_AVAILABLE:
            if retinaface_path.exists():
                self.retinaface_hef = HEF(str(retinaface_path))
            if arcface_path.exists():
                self.arcface_hef = HEF(str(arcface_path))

    def _load_enrolled_faces(self):
        """Load enrolled faces from local storage."""
        faces_dir = self.config.enrolled_faces_path
        if not faces_dir.exists():
            try:
                faces_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                # In restricted environments (e.g., read-only test FS), skip loading
                return

        for face_file in faces_dir.glob("*.json"):
            with face_file.open() as f:
                data = json.load(f)
                self.enrolled_faces[data["face_id"]] = {
                    "name": data["name"],
                    "role": data["role"],
                    "embedding": np.array(data["embedding"]),
                }

    def detect_faces(self, frame: np.ndarray) -> list[FaceResult]:
        """Detect faces in frame."""
        if not HAILO_AVAILABLE or self.retinaface_hef is None:
            return []

        _ = frame
        # TODO: implement RetinaFace inference and parsing
        return []

    def get_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """Generate 512-dimensional face embedding."""
        if not HAILO_AVAILABLE or self.arcface_hef is None:
            return np.zeros(512)

        _ = face_crop
        # TODO: align, preprocess and run ArcFace inference
        return np.zeros(512)

    def find_match(self, embedding: np.ndarray) -> FaceMatch | None:
        """Find matching enrolled face."""
        if not self.enrolled_faces:
            return None

        best_match = None
        best_score = 0.0

        for face_id, data in self.enrolled_faces.items():
            enrolled_emb = data["embedding"]
            similarity = np.dot(embedding, enrolled_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(enrolled_emb)
            )

            if (
                similarity > self.config.face_match_threshold
                and similarity > best_score
            ):
                best_score = similarity
                best_match = FaceMatch(
                    face_id=face_id, name=data["name"], confidence=float(similarity)
                )

        return best_match

    def enroll_face(self, face_id: str, images: list[np.ndarray], metadata: dict) -> bool:
        """Enroll a new face."""
        embeddings = []

        for img in images:
            faces = self.detect_faces(img)
            if faces:
                embedding = self.get_embedding(img)
                if np.any(embedding):
                    embeddings.append(embedding)

        if not embeddings:
            return False

        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)

        face_data = {
            "face_id": face_id,
            "name": metadata["name"],
            "role": metadata.get("role", "driver"),
            "notes": metadata.get("notes", ""),
            "embedding": avg_embedding.tolist(),
            "enrolled_at": metadata.get("enrolled_at", datetime.now().isoformat()),
        }

        face_path = self.config.enrolled_faces_path / f"{face_id}.json"
        with face_path.open("w") as f:
            json.dump(face_data, f)

        self.enrolled_faces[face_id] = {
            "name": face_data["name"],
            "role": face_data["role"],
            "embedding": avg_embedding,
        }

        return True

    def delete_enrolled_face(self, face_id: str) -> bool:
        """Delete an enrolled face."""
        face_path = self.config.enrolled_faces_path / f"{face_id}.json"
        if face_path.exists():
            face_path.unlink()

        if face_id in self.enrolled_faces:
            del self.enrolled_faces[face_id]
            return True
        return False

    def list_enrolled_faces(self) -> list[dict]:
        """List all enrolled faces."""
        return [
            {"face_id": fid, "name": data["name"], "role": data["role"]}
            for fid, data in self.enrolled_faces.items()
        ]
