# Tesla Dashcam AI Pipeline: Updated Architecture

## Confirmed Decisions

| Decision | Choice | Notes |
|----------|--------|-------|
| **NEVDIS Broker** | TBD - comparison below | Need to contact for pricing |
| **Face Enrollment** | Dashboard Touch UI | On-device enrollment flow |
| **Watchlist Alerts** | ALL hits | Stolen, WOVR, Expired Rego, PPSR, Custom |
| **Footage Retention** | Keep ALL | TeslaCam + Pi camera, indefinite cloud storage |

---

## NEVDIS Broker Comparison

Both brokers require contacting for pricing (not published). Here's what we know:

| Feature | MotorWeb | InfoAgent | BlueFlag |
|---------|----------|-----------|----------|
| **Market Position** | Largest AU broker | 100K+ requests/day | Smaller, simpler |
| **API Type** | REST + XML | REST | REST |
| **Products** | AutoReport, AutoReport-PLUS | Customizable fields | Basic NEVDIS |
| **Stolen Check** | ✅ All jurisdictions | ✅ All jurisdictions | ✅ |
| **WOVR History** | ✅ Full history | ✅ Full history | ✅ |
| **PPSR** | ✅ Integrated | ✅ Integrated | ❌ Separate |
| **Rego Expiry** | ✅ | ✅ | ✅ |
| **Make/Model/Colour** | ✅ | ✅ | ✅ |
| **VIN Decode** | ✅ | ✅ | ✅ |
| **Valuation Data** | ✅ (Glasses/Redbook) | ❌ | ❌ |
| **Batch Processing** | ✅ | ✅ | ✅ |
| **Est. Price Range** | $0.15-0.50/lookup | $0.20-0.40/lookup | $0.25/lookup |
| **Volume Discounts** | ✅ | ✅ | ✅ |
| **Industries** | Insurance, Fleet, Parking, Law Enforcement | Insurance, Finance, Fleet | General |

### Recommendation

**Contact both MotorWeb and InfoAgent** for quotes. Key questions:
1. Per-lookup pricing for AutoReport equivalent (plate → full vehicle + flags)
2. Volume discounts at 100/day (~3,000/month)
3. API rate limits
4. Minimum commitment / setup fees
5. Test/sandbox environment

For this project, we need:
- Plate → Make/Model/Year/Colour
- Rego status + expiry
- Stolen flag + jurisdiction
- WOVR status + type
- Real-time API (< 500ms response)

---

## Face Enrollment UI (Dashboard Touch)

### Enrollment Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FACE ENROLLMENT SCREEN (800×480)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 1: ENTER DETAILS                                                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  Name: [____________________] ← Touch to open keyboard                  ││
│  │                                                                          ││
│  │  Role: [Driver ▼]  ← Dropdown: Driver, Passenger, Blocked               ││
│  │                                                                          ││
│  │  Notes: [____________________]  (Optional)                               ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│                              [Next →]                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    FACE ENROLLMENT SCREEN (800×480)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 2: CAPTURE FACES (3 angles required)                                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌───────────────────────────────────┐  ┌─────────────────────────────────┐ │
│  │                                    │  │ CAPTURED: 1/3                   │ │
│  │                                    │  │                                 │ │
│  │      ┌─────────────────────┐      │  │  ┌─────┐                        │ │
│  │      │                     │      │  │  │ ✓   │  Front                 │ │
│  │      │    [LIVE CAMERA]    │      │  │  └─────┘                        │ │
│  │      │                     │      │  │                                 │ │
│  │      │   ┌───────────┐     │      │  │  ┌─────┐                        │ │
│  │      │   │  FACE OK  │     │      │  │  │     │  Left profile          │ │
│  │      │   │  ✓ Green  │     │      │  │  └─────┘                        │ │
│  │      │   └───────────┘     │      │  │                                 │ │
│  │      │                     │      │  │  ┌─────┐                        │ │
│  │      └─────────────────────┘      │  │  │     │  Right profile         │ │
│  │                                    │  │  └─────┘                        │ │
│  │         [📷 CAPTURE]               │  │                                 │ │
│  │                                    │  │ Turn head slightly for next    │ │
│  └───────────────────────────────────┘  └─────────────────────────────────┘ │
│                                                                              │
│  [← Back]                                              [Skip] [Complete →]  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    FACE ENROLLMENT SCREEN (800×480)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 3: CONFIRM ENROLLMENT                                                  │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │     ┌─────┐  ┌─────┐  ┌─────┐                                           ││
│  │     │     │  │     │  │     │   Captured images                         ││
│  │     │ 👤  │  │ 👤  │  │ 👤  │   (stored locally only)                   ││
│  │     └─────┘  └─────┘  └─────┘                                           ││
│  │                                                                          ││
│  │     Name:  Daniel Borrowman                                             ││
│  │     Role:  Driver                                                        ││
│  │     Notes: Primary driver                                                ││
│  │                                                                          ││
│  │     ⚠️ Face data stored on device only.                                 ││
│  │        Only embeddings synced to cloud for fleet matching.              ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  [← Retake]                                              [✓ Confirm]        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Enrollment Implementation

```python
# ui/screens/face_enroll_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.clock import Clock
from core.face_recognition import FaceRecognitionPipeline

class FaceEnrollScreen(Screen):
    name_input = StringProperty('')
    role = StringProperty('Driver')
    notes = StringProperty('')
    captured_images = ListProperty([])
    capture_count = NumericProperty(0)
    required_captures = 3
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.face_pipeline = FaceRecognitionPipeline()
        self.camera_active = False
        self.current_frame = None
        
    def on_enter(self):
        """Start camera preview when entering screen."""
        self.camera_active = True
        Clock.schedule_interval(self.update_preview, 1/30)
    
    def on_leave(self):
        """Stop camera when leaving screen."""
        self.camera_active = False
        Clock.unschedule(self.update_preview)
    
    def update_preview(self, dt):
        """Update camera preview and check for face."""
        if not self.camera_active:
            return
        
        frame = self.app.camera.get_frame()
        if frame is None:
            return
        
        self.current_frame = frame
        
        # Check if face is detected and quality is good
        faces = self.face_pipeline.detect_faces(frame)
        
        if faces and len(faces) == 1:
            face = faces[0]
            # Check face quality
            if self._check_face_quality(face):
                self.ids.face_indicator.color = 'green'
                self.ids.face_indicator.text = 'FACE OK'
                self.ids.capture_btn.disabled = False
            else:
                self.ids.face_indicator.color = 'yellow'
                self.ids.face_indicator.text = 'ADJUST POSITION'
                self.ids.capture_btn.disabled = True
        else:
            self.ids.face_indicator.color = 'red'
            self.ids.face_indicator.text = 'NO FACE' if not faces else 'MULTIPLE FACES'
            self.ids.capture_btn.disabled = True
        
        # Update preview image
        self.ids.camera_preview.texture = self._frame_to_texture(frame)
    
    def _check_face_quality(self, face) -> bool:
        """Check if face is suitable for enrollment."""
        # Face should be:
        # - Large enough (> 100px)
        # - Centered in frame
        # - Not too rotated
        # - Good lighting (not too dark/bright)
        
        bbox = face.bbox
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        if width < 100 or height < 100:
            return False
        
        # Check centering (face center within middle 60% of frame)
        frame_center_x = self.current_frame.shape[1] / 2
        face_center_x = (bbox[0] + bbox[2]) / 2
        if abs(face_center_x - frame_center_x) > frame_center_x * 0.3:
            return False
        
        return True
    
    def capture_face(self):
        """Capture current face for enrollment."""
        if self.current_frame is None:
            return
        
        faces = self.face_pipeline.detect_faces(self.current_frame)
        if not faces:
            return
        
        face = faces[0]
        
        # Crop and align face
        aligned_face = self.face_pipeline.align_face(self.current_frame, face.landmarks)
        
        # Store captured image
        self.captured_images.append(aligned_face)
        self.capture_count += 1
        
        # Update UI
        self._update_capture_thumbnails()
        
        # Provide feedback
        self._show_capture_feedback()
        
        if self.capture_count >= self.required_captures:
            self.ids.complete_btn.disabled = False
    
    def complete_enrollment(self):
        """Finalize face enrollment."""
        if self.capture_count < 1:
            return
        
        # Generate face ID
        face_id = f"face_{int(time.time())}_{self.name_input.replace(' ', '_')}"
        
        # Enroll face using captured images
        success = self.face_pipeline.enroll_face(
            face_id=face_id,
            images=self.captured_images,
            metadata={
                'name': self.name_input,
                'role': self.role,
                'notes': self.notes,
                'enrolled_at': datetime.now().isoformat()
            }
        )
        
        if success:
            # Show success message
            self._show_success_dialog(face_id)
            
            # Sync embedding to cloud (optional, for fleet matching)
            if self.app.config.get('sync_faces_to_cloud', False):
                self._sync_face_to_cloud(face_id)
            
            # Return to main screen
            self.manager.current = 'main'
        else:
            self._show_error_dialog("Failed to enroll face. Please try again.")
    
    def _sync_face_to_cloud(self, face_id: str):
        """Sync face embedding to Cloudflare Vectorize for fleet matching."""
        embedding = self.face_pipeline.get_embedding(face_id)
        
        # Send only embedding (no images) to cloud
        self.app.cloud_service.sync_face_embedding(
            face_id=face_id,
            embedding=embedding.tolist(),
            metadata={
                'name': self.name_input,
                'role': self.role,
                'vehicle_id': self.app.vehicle_id
            }
        )


class FaceManageScreen(Screen):
    """Screen for managing enrolled faces."""
    
    enrolled_faces = ListProperty([])
    
    def on_enter(self):
        self.load_enrolled_faces()
    
    def load_enrolled_faces(self):
        """Load all enrolled faces from local storage."""
        self.enrolled_faces = self.app.face_pipeline.list_enrolled_faces()
    
    def delete_face(self, face_id: str):
        """Delete an enrolled face."""
        # Confirm dialog
        self._show_confirm_dialog(
            f"Delete {face_id}?",
            on_confirm=lambda: self._do_delete_face(face_id)
        )
    
    def _do_delete_face(self, face_id: str):
        """Actually delete the face."""
        self.app.face_pipeline.delete_enrolled_face(face_id)
        
        # Also remove from cloud if synced
        if self.app.config.get('sync_faces_to_cloud', False):
            self.app.cloud_service.delete_face_embedding(face_id)
        
        self.load_enrolled_faces()
```

---

## Watchlist Alert Configuration

All watchlist matches trigger alerts. Priority determines notification urgency:

| Watchlist | Priority | Alert Type | Notification |
|-----------|----------|------------|--------------|
| **Stolen Vehicle** | 🔴 CRITICAL | Immediate | Push + SMS + Sound + Dashboard Flash |
| **WOVR Statutory** | 🟠 HIGH | Immediate | Push + Dashboard |
| **WOVR Repairable** | 🟡 MEDIUM | Logged | Dashboard |
| **Expired Rego** | 🟡 MEDIUM | Logged | Dashboard |
| **PPSR Encumbered** | 🟡 MEDIUM | Logged | Dashboard |
| **Custom Watchlist** | Configurable | Configurable | Configurable |

### Alert Worker (All Watchlists)

```typescript
// workers/watchlist-alert.ts
interface WatchlistMatch {
  type: 'stolen' | 'wovr_statutory' | 'wovr_repairable' | 'expired_rego' | 'ppsr' | 'custom';
  priority: 'critical' | 'high' | 'medium' | 'low';
  plate: string;
  vehicle_data: any;
  location: { lat: number; lng: number };
  timestamp: string;
}

const ALERT_CONFIG = {
  stolen: {
    priority: 'critical',
    push: true,
    sms: true,
    sound: true,
    flash: true
  },
  wovr_statutory: {
    priority: 'high',
    push: true,
    sms: false,
    sound: true,
    flash: false
  },
  wovr_repairable: {
    priority: 'medium',
    push: false,
    sms: false,
    sound: false,
    flash: false
  },
  expired_rego: {
    priority: 'medium',
    push: false,
    sms: false,
    sound: false,
    flash: false
  },
  ppsr: {
    priority: 'medium',
    push: false,
    sms: false,
    sound: false,
    flash: false
  },
  custom: {
    priority: 'configurable',
    push: true,
    sms: false,
    sound: true,
    flash: false
  }
};

export async function processWatchlistMatch(
  env: Env, 
  match: WatchlistMatch
): Promise<void> {
  const config = ALERT_CONFIG[match.type];
  
  // 1. Store alert in D1
  await env.DB.prepare(`
    INSERT INTO watchlist_alerts (
      alert_id, plate_number, alert_type, priority,
      vehicle_make, vehicle_model, vehicle_colour,
      gps_lat, gps_lng, timestamp, details
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    crypto.randomUUID(),
    match.plate,
    match.type,
    config.priority,
    match.vehicle_data?.make,
    match.vehicle_data?.model,
    match.vehicle_data?.colour,
    match.location.lat,
    match.location.lng,
    match.timestamp,
    JSON.stringify(match.vehicle_data)
  ).run();
  
  // 2. Update KV for dashboard real-time display
  await env.KV.put(
    `alert:latest:${match.plate}`,
    JSON.stringify(match),
    { expirationTtl: 3600 }
  );
  
  // 3. Push to Dashboard Durable Object
  const dashboard = env.DASHBOARD.get(
    env.DASHBOARD.idFromName('fleet-dashboard')
  );
  await dashboard.fetch(new Request('https://internal/alert', {
    method: 'POST',
    body: JSON.stringify({
      type: 'watchlist_alert',
      priority: config.priority,
      data: match
    })
  }));
  
  // 4. Queue notifications based on config
  if (config.push || config.sms) {
    await env.NOTIFICATION_QUEUE.send({
      type: 'watchlist_notification',
      channels: {
        push: config.push,
        sms: config.sms
      },
      alert: match
    });
  }
}
```

### Dashboard Alert Display

```python
# ui/widgets/alert_card.py
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty
from kivy.animation import Animation

class AlertCard(BoxLayout):
    plate = StringProperty('')
    alert_type = StringProperty('')
    priority = StringProperty('medium')
    vehicle_info = StringProperty('')
    timestamp = StringProperty('')
    is_critical = BooleanProperty(False)
    
    PRIORITY_COLORS = {
        'critical': (0.8, 0.1, 0.1, 1),  # Red
        'high': (0.9, 0.5, 0.1, 1),       # Orange
        'medium': (0.9, 0.8, 0.1, 1),     # Yellow
        'low': (0.5, 0.5, 0.5, 1)         # Gray
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(priority=self._update_color)
        self.bind(is_critical=self._start_flash)
    
    def _update_color(self, instance, priority):
        self.background_color = self.PRIORITY_COLORS.get(priority, (0.2, 0.2, 0.2, 1))
    
    def _start_flash(self, instance, is_critical):
        if is_critical:
            # Flash animation for critical alerts
            anim = Animation(
                background_color=(1, 0, 0, 1),
                duration=0.3
            ) + Animation(
                background_color=(0.3, 0, 0, 1),
                duration=0.3
            )
            anim.repeat = True
            anim.start(self)
            
            # Play alert sound
            self.app.play_alert_sound('critical')
```

---

## Footage Retention Strategy

### Keep ALL Footage

| Source | Local Storage | Cloud Storage | Retention |
|--------|---------------|---------------|-----------|
| **TeslaCam RecentClips** | 200GB NVMe (rolling) | R2 (all uploaded) | Indefinite |
| **TeslaCam SavedClips** | NVMe | R2 | Indefinite |
| **TeslaCam SentryClips** | NVMe | R2 (priority) | Indefinite |
| **Pi Camera** | 50GB NVMe (rolling) | R2 (all uploaded) | Indefinite |

### Upload Strategy

```python
# services/footage_sync.py
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

class FootageSyncService:
    def __init__(self, config):
        self.teslacam_path = Path('/mnt/teslacam/TeslaCam')
        self.pi_footage_path = Path('/data/pi_footage')
        self.upload_queue = asyncio.PriorityQueue()
        self.r2_client = R2Client(config)
        
    async def monitor_new_clips(self):
        """Watch for new clips and queue for upload."""
        while True:
            # Check TeslaCam directories
            for subdir in ['SentryClips', 'SavedClips', 'RecentClips']:
                path = self.teslacam_path / subdir
                for clip in path.glob('**/*.mp4'):
                    if not self._is_uploaded(clip):
                        priority = self._get_priority(subdir, clip)
                        await self.upload_queue.put((priority, clip))
            
            # Check Pi camera footage
            for clip in self.pi_footage_path.glob('*.mp4'):
                if not self._is_uploaded(clip):
                    await self.upload_queue.put((2, clip))  # Medium priority
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def _get_priority(self, subdir: str, clip: Path) -> int:
        """
        Priority: 0 = highest (upload first)
        - Sentry clips with alerts: 0
        - Saved clips: 1
        - Sentry clips (no alert): 1
        - Recent clips: 2
        """
        if subdir == 'SentryClips':
            # Check if this clip has a watchlist alert
            if self._has_watchlist_alert(clip):
                return 0
            return 1
        elif subdir == 'SavedClips':
            return 1
        else:  # RecentClips
            return 2
    
    async def process_upload_queue(self):
        """Process upload queue, uploading clips to R2."""
        while True:
            priority, clip = await self.upload_queue.get()
            
            try:
                await self._upload_clip(clip)
                self._mark_uploaded(clip)
            except Exception as e:
                # Re-queue with lower priority on failure
                await self.upload_queue.put((priority + 1, clip))
                await asyncio.sleep(60)  # Wait before retry
            
            # Rate limit uploads to avoid saturating LTE
            await asyncio.sleep(5)
    
    async def _upload_clip(self, clip: Path):
        """Upload a clip to R2."""
        # Determine R2 path
        relative_path = clip.relative_to(self.teslacam_path.parent)
        r2_key = f"footage/{self.vehicle_id}/{relative_path}"
        
        # Upload with metadata
        await self.r2_client.upload_file(
            key=r2_key,
            file_path=clip,
            metadata={
                'vehicle_id': self.vehicle_id,
                'source': 'teslacam' if 'TeslaCam' in str(clip) else 'pi_camera',
                'captured_at': self._get_clip_timestamp(clip).isoformat(),
                'uploaded_at': datetime.utcnow().isoformat()
            }
        )
        
        # Trigger processing workflow
        await self._trigger_processing_workflow(r2_key)
```

### R2 Storage Cost Estimate

| Footage Type | Daily Volume | Monthly Volume | R2 Cost |
|--------------|--------------|----------------|---------|
| TeslaCam (all) | ~10GB | ~300GB | $4.50 |
| Pi Camera | ~5GB | ~150GB | $2.25 |
| Processed (Stream) | ~2GB | ~60GB | $0.90 |
| **Total** | ~17GB/day | ~510GB | **~$7.65/month** |

*R2 pricing: $0.015/GB/month storage, egress free*

---

## Updated Cost Summary

| Component | Monthly (AUD) |
|-----------|---------------|
| **NEVDIS API** | $50-75 (TBD) |
| **Cloudflare Workers** | $5 |
| **D1 Database** | $5 |
| **KV + Durable Objects** | $5 |
| **R2 Storage (510GB)** | $8 |
| **Stream Transcoding** | $36 |
| **Workers AI** | $5 |
| **LTE Data (~10GB)** | $20 |
| **TOTAL** | **~$140-165 AUD/month** |

---

## Next Actions

1. **Contact NEVDIS Brokers**
   - MotorWeb: https://www.motorweb.au/contact
   - InfoAgent: https://www.infoagent.com.au/contact
   - Request: API access, pricing for 3,000 lookups/month, test environment

2. **Order Hardware** (~$590 AUD)
   - Pi 5 8GB
   - Hailo-8L M.2 HAT
   - 256GB NVMe
   - 5" 800×480 display
   - USB camera, GPS, LTE modem

3. **Prepare Hailo Models**
   - Download pre-trained: YOLOv8-Nano, RetinaFace, ArcFace, LPRNet
   - Compile to HEF format using Hailo Dataflow Compiler

4. **Prototype USB Gadget Mode**
   - Test `g_mass_storage` with Model 3
   - Verify TeslaCam folder structure recognized
   - Test concurrent read (Pi) while Tesla writes

5. **Set Up Cloudflare Infrastructure**
   - D1 database with schema
   - R2 buckets (raw, processed)
   - Workers (alert, rego, face)
   - Vectorize indexes
