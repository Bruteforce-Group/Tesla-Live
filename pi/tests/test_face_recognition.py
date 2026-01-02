import numpy as np

from core.config import settings
from core.face_recognition import FaceRecognitionPipeline


def test_face_pipeline_no_faces():
    pipeline = FaceRecognitionPipeline(settings)
    faces = pipeline.detect_faces(np.zeros((10, 10, 3)))
    assert faces == []
