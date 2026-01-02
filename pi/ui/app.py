from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from core.camera import CameraManager
from core.config import settings
from core.detector import HailoDetector
from core.face_recognition import FaceRecognitionPipeline
from core.gps import GPSManager
from core.plate_ocr import PlateOCR
from services.alert_service import AlertService
from services.rego_service import RegoService
from services.upload_service import UploadService
from ui.screens.alerts_screen import AlertsScreen
from ui.screens.detections_screen import DetectionsScreen
from ui.screens.face_enroll_screen import FaceEnrollScreen
from ui.screens.face_manage_screen import FaceManageScreen
from ui.screens.main_screen import MainScreen
from ui.screens.settings_screen import SettingsScreen


class DashcamApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings

        Builder.load_file("ui/dashboard.kv")

        # Initialize services
        self.camera = CameraManager(settings)
        self.detector = HailoDetector(settings)
        self.plate_ocr = PlateOCR(settings)
        self.face_pipeline = FaceRecognitionPipeline(settings)
        self.gps = GPSManager(settings)
        self.alert_service = AlertService(settings)
        self.rego_service = RegoService(settings)
        self.upload_service = UploadService(settings)

        # State
        self.is_recording = False
        self.session_stats = {
            "plates": 0,
            "faces": 0,
            "persons": 0,
            "alerts": 0,
        }

    def build(self):
        Window.size = self.settings.display_resolution

        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(DetectionsScreen(name="detections"))
        sm.add_widget(AlertsScreen(name="alerts"))
        sm.add_widget(FaceEnrollScreen(name="face_enroll"))
        sm.add_widget(FaceManageScreen(name="face_manage"))
        sm.add_widget(SettingsScreen(name="settings"))

        return sm

    def on_start(self):
        self.camera.start()
        self.is_recording = True

        self.gps.start()

        Clock.schedule_interval(self.process_frame, 1.0 / self.settings.detection_fps)
        Clock.schedule_interval(self.update_ui, 0.5)
        Clock.schedule_interval(self.sync_to_cloud, 30)

    def on_stop(self):
        self.camera.stop()
        self.gps.stop()

    def process_frame(self, _dt):
        """Main processing loop - runs at detection_fps."""
        frame = self.camera.get_frame()
        if frame is None:
            return

        detections = self.detector.detect(frame.image)
        gps_data = self.gps.get_current()

        for det in detections:
            if hasattr(det, "plate_crop") and det.plate_crop is not None:
                plate_result = self.plate_ocr.recognize(det.plate_crop)
                if (
                    plate_result
                    and plate_result.confidence > self.settings.plate_confidence_threshold
                ):
                    self.session_stats["plates"] += 1
                    self._handle_plate_detection(plate_result, gps_data, frame.timestamp)

            if det.class_name == "person":
                self.session_stats["persons"] += 1
                person_crop = self._crop_detection(frame.image, det.bbox)
                faces = self.face_pipeline.detect_faces(person_crop)
                for face in faces:
                    self.session_stats["faces"] += 1
                    self._handle_face_detection(face, gps_data, frame.timestamp)

    def _handle_plate_detection(self, plate_result, gps_data, timestamp):
        """Handle a plate detection - queue for NEVDIS lookup."""
        self.rego_service.queue_lookup(
            {
                "plate_number": plate_result.text,
                "plate_state": plate_result.state,
                "confidence": plate_result.confidence,
                "timestamp": timestamp.isoformat(),
                "gps_lat": gps_data.latitude if gps_data else None,
                "gps_lng": gps_data.longitude if gps_data else None,
            }
        )

    def _handle_face_detection(self, face_result, gps_data, timestamp):
        """Handle a face detection - check for match."""
        if face_result.match:
            payload = {
                "matched_face_id": face_result.match.face_id,
                "match_confidence": face_result.match.confidence,
                "timestamp": timestamp.isoformat(),
                "gps_lat": gps_data.latitude if gps_data else None,
                "gps_lng": gps_data.longitude if gps_data else None,
            }
            # Fire and forget
            import asyncio

            self._last_alert_task = asyncio.create_task(
                self.alert_service.send_face_sighting(payload)
            )

    def _crop_detection(self, frame, bbox):
        x1, y1, x2, y2 = map(int, [bbox.x1, bbox.y1, bbox.x2, bbox.y2])
        return frame[y1:y2, x1:x2]

    def update_ui(self, _dt):
        """Update dashboard UI."""
        main_screen = self.root.get_screen("main")
        main_screen.update_stats(
            speed=self.gps.speed,
            heading=self.gps.heading,
            location=self.gps.location_name,
            **self.session_stats,
        )
        main_screen.update_status(
            lte_connected=self.upload_service.is_connected,
            gps_locked=self.gps.has_fix,
            recording=self.is_recording,
        )

    def sync_to_cloud(self, _dt):
        """Background cloud sync."""
        self.upload_service.process_queue()
        self.rego_service.process_queue()

    def capture_clip(self):
        """Placeholder for UI clip capture button."""
        # TODO: integrate ClipService with camera buffer
        return None


if __name__ == "__main__":
    DashcamApp().run()
