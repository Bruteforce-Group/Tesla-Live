from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Device
    vehicle_id: str = Field(default="tesla-001")
    device_id: str = Field(default="pi-001")

    # Paths
    teslacam_mount: Path = Field(default=Path("/mnt/teslacam"))
    pi_footage_path: Path = Field(default=Path("/data/pi_footage"))
    models_path: Path = Field(default=Path("/opt/dashcam/models"))
    local_db_path: Path = Field(default=Path("/data/dashcam.db"))
    enrolled_faces_path: Path = Field(default=Path("/data/faces"))

    # Cloud
    api_base_url: str = Field(default="https://tesla-dashcam-api.workers.dev")
    api_key: str = Field(default="")

    # NEVDIS
    nevdis_api_url: str = Field(default="https://api.motorweb.com.au/v1")
    nevdis_api_key: str = Field(default="")

    # Camera
    camera_resolution: tuple[int, int] = Field(default=(1920, 1080))
    camera_fps: int = Field(default=30)

    # Detection
    detection_fps: int = Field(default=10)  # Process every 3rd frame
    plate_confidence_threshold: float = Field(default=0.7)
    face_confidence_threshold: float = Field(default=0.8)
    face_match_threshold: float = Field(default=0.6)

    # Upload
    upload_on_wifi_only: bool = Field(default=False)
    upload_priority_sentry: bool = Field(default=True)

    # Display
    display_resolution: tuple[int, int] = Field(default=(800, 480))

    class Config:
        env_file = ".env"
        env_prefix = "DASHCAM_"


settings = Settings()
