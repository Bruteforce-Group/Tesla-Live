# Tesla Model 3 Dashcam AI Pipeline: Final Architecture

## System Overview

A Raspberry Pi 5 connected to a Tesla Model 3 via **USB Gadget Mode**, acting as both a TeslaCam storage device and an independent AI-powered dashcam system with Australian vehicle registration lookups, stolen vehicle alerts, and on-device facial recognition.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     TESLA MODEL 3 + RPI5 INTEGRATION                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                        TESLA MODEL 3                                         ││
│  │                                                                              ││
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                ││
│  │  │   TeslaCam   │     │   Sentry     │     │   USB Port   │                ││
│  │  │   Cameras    │────▶│    Mode      │────▶│  (Glove Box) │                ││
│  │  │  (8 cameras) │     │   Writer     │     │   USB-C/A    │                ││
│  │  └──────────────┘     └──────────────┘     └──────┬───────┘                ││
│  │                                                    │                        ││
│  │                                                    │ USB Data + Power       ││
│  │                                                    │ (5V, 2.4A)             ││
│  └────────────────────────────────────────────────────┼────────────────────────┘│
│                                                       │                         │
│                                                       ▼                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                    RASPBERRY PI 5 (USB GADGET MODE)                          ││
│  │                                                                              ││
│  │  ┌──────────────────────────────────────────────────────────────────────┐   ││
│  │  │                      USB GADGET CONFIGURATION                         │   ││
│  │  │                                                                        │   ││
│  │  │  g_mass_storage module emulates USB flash drive                       │   ││
│  │  │  ├─ /dev/loop0 → TeslaCam partition (exFAT, ~200GB)                  │   ││
│  │  │  │              └─ /TeslaCam/RecentClips                              │   ││
│  │  │  │              └─ /TeslaCam/SavedClips                               │   ││
│  │  │  │              └─ /TeslaCam/SentryClips                              │   ││
│  │  │  │                                                                    │   ││
│  │  │  └─ Simultaneously mounted read-only by Pi for processing            │   ││
│  │  │                                                                        │   ││
│  │  └──────────────────────────────────────────────────────────────────────┘   ││
│  │                                                                              ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            ││
│  │  │  Hailo-8L  │  │ USB Camera │  │  LTE Modem │  │ 5" Touch   │            ││
│  │  │  13 TOPS   │  │  1080p30   │  │    4G/5G   │  │  800×480   │            ││
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘            ││
│  │        │               │               │               │                    ││
│  │        └───────────────┴───────────────┴───────────────┘                    ││
│  │                                │                                             ││
│  │                                ▼                                             ││
│  │  ┌──────────────────────────────────────────────────────────────────────┐   ││
│  │  │                    ON-DEVICE AI PROCESSING                            │   ││
│  │  │                                                                        │   ││
│  │  │  Hailo-8L Models:                                                     │   ││
│  │  │  ├─ YOLOv8-Nano: Vehicles, persons, signs (~15ms)                    │   ││
│  │  │  ├─ License Plate Detector: AU plate localizer (~10ms)               │   ││
│  │  │  ├─ LPRNet: Plate character OCR (~8ms)                               │   ││
│  │  │  ├─ RetinaFace: Face detection (~12ms)                               │   ││
│  │  │  └─ ArcFace: Face embedding 512-dim (~15ms)                          │   ││
│  │  │                                                                        │   ││
│  │  │  Total pipeline: ~60ms per frame (16+ FPS capable)                   │   ││
│  │  └──────────────────────────────────────────────────────────────────────┘   ││
│  │                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Hardware Configuration

### Bill of Materials

| Component | Model | Purpose | Est. Cost (AUD) |
|-----------|-------|---------|-----------------|
| **Raspberry Pi 5** | 8GB RAM | Main compute | $120 |
| **Hailo-8L M.2** | 13 TOPS NPU | Edge AI acceleration | $110 |
| **M.2 HAT+** | Official Pi HAT | Hailo connection | $25 |
| **NVMe SSD** | 256GB Gen3 | TeslaCam storage + OS | $50 |
| **5" Display** | 800×480 IPS Capacitive | Dashboard UI | $70 |
| **USB Camera** | 1080p30 wide-angle | Independent recording | $45 |
| **LTE Modem** | Quectel EC25-AU | 4G connectivity | $80 |
| **GPS Module** | u-blox NEO-M8N | Location tracking | $35 |
| **Accelerometer** | MPU6050 | Motion detection | $10 |
| **USB-C Cable** | Data + Power capable | Tesla connection | $15 |
| **Enclosure** | 3D printed / aluminum | Protection | $30 |
| **Total** | | | **~$590 AUD** |

### USB Gadget Mode Setup

The Pi 5 uses the `dwc2` USB controller in gadget mode to appear as a mass storage device to the Tesla:

**/boot/firmware/config.txt**:
```ini
# Enable USB gadget mode
dtoverlay=dwc2,dr_mode=peripheral
```

**/boot/firmware/cmdline.txt** (append):
```
modules-load=dwc2,g_mass_storage
```

**Gadget initialization script** (`/usr/local/bin/teslacam-gadget.sh`):
```bash
#!/bin/bash
# Create TeslaCam disk image if not exists
TESLACAM_IMG="/data/teslacam.img"
TESLACAM_SIZE="200G"
MOUNT_POINT="/mnt/teslacam"

if [ ! -f "$TESLACAM_IMG" ]; then
    truncate -s $TESLACAM_SIZE $TESLACAM_IMG
    mkfs.exfat -n TeslaCam $TESLACAM_IMG
fi

# Set up loop device
LOOP_DEV=$(losetup -f --show $TESLACAM_IMG)

# Mount for Pi access (read-only to prevent corruption)
mkdir -p $MOUNT_POINT
mount -o ro,loop $TESLACAM_IMG $MOUNT_POINT

# Create required TeslaCam folders if missing
for dir in RecentClips SavedClips SentryClips; do
    mkdir -p $MOUNT_POINT/TeslaCam/$dir 2>/dev/null || true
done

# Load USB gadget module - Tesla sees this as a USB drive
modprobe g_mass_storage \
    file=$TESLACAM_IMG \
    stall=0 \
    ro=0 \
    removable=1 \
    idVendor=0x0781 \
    idProduct=0x5572 \
    bcdDevice=0x0100 \
    iManufacturer="SanDisk" \
    iProduct="Cruzer Blade" \
    iSerialNumber="$(cat /proc/sys/kernel/random/uuid | cut -d'-' -f1)"

echo "TeslaCam gadget active on $LOOP_DEV"
```

**Key considerations**:
- Tesla writes to the USB drive continuously while driving
- Pi monitors `/mnt/teslacam/TeslaCam/` for new clips
- On WiFi connection or LTE, clips are processed and uploaded
- Filesystem corruption handling via periodic fsck

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              COMPLETE DATA FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                    INPUT SOURCES (Dual Camera System)                            │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                                                                                  │
│  [Tesla Cameras]                          [Pi USB Camera]                        │
│       │                                        │                                 │
│       │ TeslaCam writes to                     │ Direct capture                  │
│       │ USB gadget storage                     │ 1080p @ 30fps                   │
│       │                                        │                                 │
│       ▼                                        ▼                                 │
│  /mnt/teslacam/TeslaCam/              [Camera Manager]                          │
│  ├─ RecentClips/ (1hr rolling)              │                                   │
│  ├─ SavedClips/ (manual saves)              │ Frame buffer                      │
│  └─ SentryClips/ (motion events)            │ (10s circular)                    │
│       │                                        │                                 │
│       └────────────────┬───────────────────────┘                                │
│                        │                                                         │
│                        ▼                                                         │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                    ON-DEVICE PROCESSING (Hailo-8L)                               │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                     HAILO INFERENCE PIPELINE                              │   │
│  │                                                                            │   │
│  │  Frame ──► YOLOv8-Nano ──┬──► Vehicle Detection ──► Plate Detector       │   │
│  │            (15ms)        │                              │                 │   │
│  │                          │                              ▼                 │   │
│  │                          │                         LPRNet OCR             │   │
│  │                          │                         "ABC-123"              │   │
│  │                          │                              │                 │   │
│  │                          ├──► Person Detection ──► RetinaFace            │   │
│  │                          │                              │                 │   │
│  │                          │                              ▼                 │   │
│  │                          │                         ArcFace Embed          │   │
│  │                          │                         [512-dim vector]       │   │
│  │                          │                                                │   │
│  │                          └──► Sign/Signal Detection                      │   │
│  │                                                                            │   │
│  │  Total: ~60ms/frame = 16 FPS                                             │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                        │                                                         │
│                        ▼                                                         │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                    CLOUD PATHS (via LTE)                                         │
│  ══════════════════════════════════════════════════════════════════════════════ │
│                                                                                  │
│       ┌────────────────┬────────────────┬────────────────┬──────────────────┐   │
│       │                │                │                │                  │   │
│       ▼                ▼                ▼                ▼                  │   │
│   HOT PATH         REGO PATH       FACE PATH        COLD PATH              │   │
│   (Alerts)         (NEVDIS)       (Matching)       (Full Video)            │   │
│                                                                              │   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │   │
│  │ Event JSON  │ │ Plate Text  │ │Face Embedding│ │ TeslaCam + Pi Video│    │   │
│  │ < 1KB       │ │ "ABC-123"   │ │ [512 floats]│ │ Clips (post-trip)  │    │   │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────────┬──────────┘    │   │
│         │               │               │                   │               │   │
│         ▼               ▼               ▼                   ▼               │   │
│  [Alert Worker]  [Rego Worker]   [Face Worker]      [R2 + Workflow]        │   │
│         │               │               │                   │               │   │
│         │               │               │                   │               │   │
├─────────┴───────────────┴───────────────┴───────────────────┴───────────────┤   │
│                                                                              │   │
│                         CLOUDFLARE SERVICES                                  │   │
│                                                                              │   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│   │
│  │                                                                          ││   │
│  │  [Workers]     [D1]        [KV]      [R2]     [Vectorize]  [Stream]    ││   │
│  │      │          │           │         │           │            │        ││   │
│  │      │    ┌─────┴─────┐     │         │     ┌─────┴─────┐      │        ││   │
│  │      │    │  Tables:  │     │         │     │  Indexes: │      │        ││   │
│  │      │    │  - trips  │     │         │     │  - faces  │      │        ││   │
│  │      │    │  - events │     │         │     │  - scenes │      │        ││   │
│  │      │    │  - plates │     │         │     │  - plates │      │        ││   │
│  │      │    │  - faces  │     │         │     │           │      │        ││   │
│  │      │    │  - watch  │     │         │     │           │      │        ││   │
│  │      │    └───────────┘     │         │     └───────────┘      │        ││   │
│  │      │                      │         │                        │        ││   │
│  │      └──────────────────────┴─────────┴────────────────────────┘        ││   │
│  │                                                                          ││   │
│  └─────────────────────────────────────────────────────────────────────────┘│   │
│                                                                              │   │
│  ══════════════════════════════════════════════════════════════════════════ │   │
│                    EXTERNAL INTEGRATIONS                                     │   │
│  ══════════════════════════════════════════════════════════════════════════ │   │
│                                                                              │   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│   │
│  │                                                                          ││   │
│  │  [NEVDIS API]              [Australian Watchlists]                      ││   │
│  │  (via MotorWeb/InfoAgent)                                               ││   │
│  │       │                          │                                       ││   │
│  │       ▼                          ▼                                       ││   │
│  │  • Rego status              • Stolen vehicles (Police)                  ││   │
│  │  • Rego expiry              • WOVR (Written-Off)                        ││   │
│  │  • Make/Model/Color         • PPSR (Encumbered)                         ││   │
│  │  • VIN lookup               • Custom fleet watchlist                    ││   │
│  │  • Stolen flag                                                           ││   │
│  │  • WOVR status                                                           ││   │
│  │                                                                          ││   │
│  └─────────────────────────────────────────────────────────────────────────┘│   │
│                                                                              │   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Australian Integrations

### NEVDIS API Integration

NEVDIS (National Exchange of Vehicle and Driver Information System) provides comprehensive vehicle data for all registered Australian vehicles. Access via authorized brokers:

| Broker | Pricing | Features |
|--------|---------|----------|
| **MotorWeb** | ~$0.15-0.50/lookup | Largest AU broker, AutoReport product |
| **InfoAgent** | ~$0.20-0.40/lookup | Stolen + WOVR included |
| **BlueFlag** | ~$0.25/lookup | Simple API, batch support |
| **CarRegistrationAPI** | $0.30/lookup | All states unified |

**Data returned per lookup**:
```json
{
  "plate": "ABC123",
  "state": "QLD",
  "rego_status": "REGISTERED",
  "rego_expiry": "2025-06-15",
  "vehicle": {
    "make": "TOYOTA",
    "model": "CAMRY",
    "series": "ASCENT",
    "year": 2019,
    "body_type": "SEDAN",
    "colour": "SILVER",
    "engine_number": "2ARFE1234567",
    "vin": "JTEBU5JR5D5012345"
  },
  "flags": {
    "stolen": false,
    "stolen_jurisdiction": null,
    "stolen_date": null,
    "wovr_status": "NOT_LISTED",
    "wovr_type": null,
    "ppsr_encumbered": false
  }
}
```

**Rego Worker implementation**:

```typescript
// workers/rego-lookup.ts
interface RegoLookupRequest {
  plate: string;
  state: string;
  vehicle_id: string;
  timestamp: string;
  gps: { lat: number; lng: number };
  confidence: number;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const lookup: RegoLookupRequest = await request.json();
    
    // Call NEVDIS broker API (MotorWeb example)
    const nevdisResponse = await fetch(
      `https://api.motorweb.com.au/v1/vehicle/plate/${lookup.plate}`,
      {
        headers: {
          'Authorization': `Bearer ${env.MOTORWEB_API_KEY}`,
          'X-State': lookup.state
        }
      }
    );
    
    const vehicleData = await nevdisResponse.json();
    
    // Check against watchlists
    const watchlistHit = await checkWatchlists(env, lookup.plate, vehicleData);
    
    // Store sighting in D1
    await env.DB.prepare(`
      INSERT INTO plate_sightings (
        sighting_id, vehicle_id, plate_number, plate_state,
        rego_status, rego_expiry, make, model, year, colour,
        stolen_flag, wovr_status, watchlist_hit,
        timestamp, gps_lat, gps_lng, confidence
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      crypto.randomUUID(),
      lookup.vehicle_id,
      lookup.plate,
      lookup.state,
      vehicleData.rego_status,
      vehicleData.rego_expiry,
      vehicleData.vehicle.make,
      vehicleData.vehicle.model,
      vehicleData.vehicle.year,
      vehicleData.vehicle.colour,
      vehicleData.flags.stolen,
      vehicleData.flags.wovr_status,
      watchlistHit?.reason || null,
      lookup.timestamp,
      lookup.gps.lat,
      lookup.gps.lng,
      lookup.confidence
    ).run();
    
    // If stolen or watchlist hit, trigger alert
    if (vehicleData.flags.stolen || watchlistHit) {
      await env.ALERT_QUEUE.send({
        type: 'watchlist_alert',
        plate: lookup.plate,
        reason: vehicleData.flags.stolen ? 'STOLEN_VEHICLE' : watchlistHit.reason,
        vehicle_data: vehicleData,
        location: lookup.gps,
        timestamp: lookup.timestamp
      });
    }
    
    return Response.json({
      success: true,
      vehicle: vehicleData,
      watchlist_hit: watchlistHit
    });
  }
};

async function checkWatchlists(env: Env, plate: string, vehicleData: any) {
  // Check custom watchlist in D1
  const customHit = await env.DB.prepare(`
    SELECT reason, priority, notes FROM plate_watchlist WHERE plate_number = ?
  `).bind(plate).first();
  
  if (customHit) {
    return { source: 'custom', ...customHit };
  }
  
  // Stolen check already in NEVDIS response
  if (vehicleData.flags.stolen) {
    return {
      source: 'nevdis_stolen',
      reason: 'STOLEN',
      priority: 'critical',
      jurisdiction: vehicleData.flags.stolen_jurisdiction,
      date: vehicleData.flags.stolen_date
    };
  }
  
  // WOVR check
  if (vehicleData.flags.wovr_status !== 'NOT_LISTED') {
    return {
      source: 'nevdis_wovr',
      reason: `WOVR_${vehicleData.flags.wovr_type}`,
      priority: vehicleData.flags.wovr_type === 'STATUTORY' ? 'high' : 'medium'
    };
  }
  
  // Expired registration
  if (vehicleData.rego_status === 'EXPIRED') {
    return {
      source: 'nevdis_rego',
      reason: 'EXPIRED_REGO',
      priority: 'low'
    };
  }
  
  return null;
}
```

### Australian Watchlists Available

| Watchlist | Source | Access Method | Use Case |
|-----------|--------|---------------|----------|
| **Stolen Vehicles** | Police (all jurisdictions) | NEVDIS API | Real-time alerts |
| **WOVR** | State transport authorities | NEVDIS API | Identify written-off vehicles |
| **PPSR** | Federal government | NEVDIS or direct PPSR API | Encumbered vehicles |
| **Unregistered** | NEVDIS | NEVDIS API | Expired registration |
| **Custom Fleet** | Your database | D1 | Track specific vehicles |
| **VIP/Blocked** | Your database | D1 | Access control |

---

## On-Device Face Recognition (Hailo-8L)

All face processing happens on-device using the Hailo-8L accelerator. No face images are sent to the cloud — only 512-dimensional embedding vectors for matching.

### Hailo Model Pipeline

```python
# core/face_recognition.py
from hailo_platform import HailoRT
import numpy as np

class FaceRecognitionPipeline:
    def __init__(self):
        self.runtime = HailoRT()
        
        # Load Hailo-compiled models
        self.detector = self.runtime.load_model('models/retinaface.hef')
        self.embedder = self.runtime.load_model('models/arcface.hef')
        
        # Local face database (enrolled faces)
        self.enrolled_faces = self._load_enrolled_faces()
    
    def process_frame(self, frame: np.ndarray) -> list[FaceResult]:
        """Detect faces and generate embeddings on-device."""
        results = []
        
        # Step 1: Detect faces with RetinaFace
        detections = self._detect_faces(frame)
        
        for det in detections:
            # Step 2: Crop and align face
            face_crop = self._align_face(frame, det.landmarks)
            
            # Step 3: Generate 512-dim embedding with ArcFace
            embedding = self._get_embedding(face_crop)
            
            # Step 4: Match against enrolled faces (local)
            match = self._find_match(embedding)
            
            results.append(FaceResult(
                bbox=det.bbox,
                confidence=det.confidence,
                embedding=embedding,
                match=match
            ))
        
        return results
    
    def _detect_faces(self, frame):
        """Run RetinaFace on Hailo (~12ms)."""
        input_tensor = self._preprocess_detector(frame)
        outputs = self.detector.infer(input_tensor)
        return self._postprocess_detector(outputs)
    
    def _get_embedding(self, face_crop):
        """Run ArcFace on Hailo (~15ms)."""
        input_tensor = self._preprocess_embedder(face_crop)
        embedding = self.embedder.infer(input_tensor)
        return embedding.flatten()
    
    def _find_match(self, embedding, threshold=0.6):
        """
        Compare embedding against enrolled faces.
        Uses cosine similarity, all computed locally.
        """
        best_match = None
        best_score = 0
        
        for face_id, enrolled_embedding in self.enrolled_faces.items():
            similarity = np.dot(embedding, enrolled_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(enrolled_embedding)
            )
            if similarity > threshold and similarity > best_score:
                best_score = similarity
                best_match = face_id
        
        if best_match:
            return FaceMatch(face_id=best_match, confidence=best_score)
        return None
    
    def enroll_face(self, face_id: str, images: list[np.ndarray]):
        """
        Enroll a new face locally.
        Average embeddings from multiple images for robustness.
        """
        embeddings = []
        for img in images:
            faces = self._detect_faces(img)
            if faces:
                embedding = self._get_embedding(
                    self._align_face(img, faces[0].landmarks)
                )
                embeddings.append(embedding)
        
        if embeddings:
            avg_embedding = np.mean(embeddings, axis=0)
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
            self.enrolled_faces[face_id] = avg_embedding
            self._save_enrolled_faces()
            return True
        return False
```

### Privacy Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FACE RECOGNITION PRIVACY MODEL                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ON-DEVICE (Raspberry Pi 5)                    CLOUD (Cloudflare)           │
│  ─────────────────────────                     ──────────────────           │
│                                                                              │
│  ┌──────────────────────┐                     ┌──────────────────────┐      │
│  │ Face Images          │                     │ Face Embeddings      │      │
│  │ • Captured locally   │                     │ • 512 floats only    │      │
│  │ • Never leave device │    ──────────►      │ • No images stored   │      │
│  │ • Deleted after      │    Embedding        │ • Cannot reconstruct │      │
│  │   processing         │    Vector Only      │   face from vector   │      │
│  └──────────────────────┘                     └──────────────────────┘      │
│                                                                              │
│  ┌──────────────────────┐                     ┌──────────────────────┐      │
│  │ Enrolled Faces       │                     │ Vectorize Index      │      │
│  │ • Stored on Pi only  │    Sync enrolled    │ • Optional cloud     │      │
│  │ • Encrypted at rest  │    embeddings for   │   matching for       │      │
│  │ • User-controlled    │    multi-device     │   fleet-wide alerts  │      │
│  │   deletion           │    ──────────►      │                      │      │
│  └──────────────────────┘                     └──────────────────────┘      │
│                                                                              │
│  ┌──────────────────────┐                     ┌──────────────────────┐      │
│  │ Face Sighting Log    │                     │ D1: Face Sightings   │      │
│  │ • Timestamp          │    Metadata only    │ • face_id (if match) │      │
│  │ • Bounding box       │    ──────────►      │ • timestamp          │      │
│  │ • Match result       │                     │ • location           │      │
│  │ • No images          │                     │ • match confidence   │      │
│  └──────────────────────┘                     └──────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Dashboard UI (800×480)

### Screen Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DASHCAM DASHBOARD (800×480)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ HEADER (40px)                                                            │ │
│ │ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌─────────────────────────────┐│ │
│ │ │🔴 REC │ │📶 4G  │ │📍 GPS │ │🔋 12V │ │ 14:32 AEST  │  02 Jan 2026 ││ │
│ │ │02:15:33│ │Strong │ │ Lock  │ │ Good  │ │             │               ││ │
│ │ └───────┘ └───────┘ └───────┘ └───────┘ └─────────────────────────────┘│ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌───────────────────────────────┐ ┌───────────────────────────────────────┐ │
│ │ LIVE STATS (200×300)          │ │ RECENT DETECTIONS (380×300)           │ │
│ │                               │ │                                       │ │
│ │  Speed:      67 km/h          │ │ ┌─────────────────────────────────┐   │ │
│ │  Heading:    NE (045°)        │ │ │ 14:31:45  ABC-123  Toyota Camry │   │ │
│ │  Location:   Albany Creek     │ │ │           Silver   QLD  ✓ Valid │   │ │
│ │                               │ │ └─────────────────────────────────┘   │ │
│ │  ┌─────────────────────────┐  │ │ ┌─────────────────────────────────┐   │ │
│ │  │ SESSION STATS           │  │ │ │ 14:30:22  XYZ-789  Ford Ranger  │   │ │
│ │  │                         │  │ │ │           White   QLD  ⚠ Exp.   │   │ │
│ │  │ 🚗 Plates:     47       │  │ │ └─────────────────────────────────┘   │ │
│ │  │ 👤 Faces:      12       │  │ │ ┌─────────────────────────────────┐   │ │
│ │  │ 🚶 Persons:    28       │  │ │ │ 14:28:55  DEF-456  Mazda CX-5   │   │ │
│ │  │ ⚠️ Alerts:      2       │  │ │ │           Red     QLD  ✓ Valid │   │ │
│ │  │                         │  │ │ └─────────────────────────────────┘   │ │
│ │  └─────────────────────────┘  │ │                                       │ │
│ │                               │ │ ┌─────────────────────────────────┐   │ │
│ │  ┌─────────────────────────┐  │ │ │ 14:25:10  ⚠️ ALERT             │   │ │
│ │  │ PIPELINE STATUS         │  │ │ │ 🚨 STOLEN: HIJ-101 Hyundai i30 │   │ │
│ │  │                         │  │ │ │ Black  NSW  Reported: 12 Dec   │   │ │
│ │  │ Upload Queue:  3        │  │ │ └─────────────────────────────────┘   │ │
│ │  │ Last Sync:     2m ago   │  │ │                                       │ │
│ │  │ NEVDIS:        Online   │  │ │                    [View All →]       │ │
│ │  │ Storage:       78% free │  │ │                                       │ │
│ │  └─────────────────────────┘  │ │                                       │ │
│ └───────────────────────────────┘ └───────────────────────────────────────┘ │
│                                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ACTION BAR (60px)                                                        │ │
│ │                                                                          │ │
│ │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│ │  │ 📷 CAPTURE  │  │ 📋 HISTORY  │  │ 👤 FACES    │  │ ⚙️ SETTINGS │    │ │
│ │  │   Clip      │  │   Events    │  │   Enroll    │  │             │    │ │
│ │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │ │
│ │                                                                          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Kivy Implementation

```python
# ui/dashboard.kv
#:kivy 2.2.0

<DashboardScreen>:
    BoxLayout:
        orientation: 'vertical'
        
        # Header Bar
        HeaderBar:
            size_hint_y: None
            height: '40dp'
        
        # Main Content
        BoxLayout:
            orientation: 'horizontal'
            padding: '10dp'
            spacing: '10dp'
            
            # Left Panel - Stats
            StatsPanel:
                size_hint_x: 0.35
            
            # Right Panel - Detections
            DetectionsPanel:
                size_hint_x: 0.65
        
        # Action Bar
        ActionBar:
            size_hint_y: None
            height: '60dp'

<HeaderBar>:
    canvas.before:
        Color:
            rgba: 0.15, 0.15, 0.15, 1
        Rectangle:
            pos: self.pos
            size: self.size
    
    BoxLayout:
        padding: '5dp'
        spacing: '10dp'
        
        StatusBadge:
            icon: 'record-circle'
            label: root.recording_time
            color: 'red' if root.is_recording else 'gray'
        
        StatusBadge:
            icon: 'signal-cellular-3'
            label: root.lte_status
            color: 'green' if root.lte_connected else 'red'
        
        StatusBadge:
            icon: 'map-marker'
            label: root.gps_status
            color: 'green' if root.gps_locked else 'yellow'
        
        StatusBadge:
            icon: 'car-battery'
            label: root.power_status
        
        Widget:  # Spacer
        
        Label:
            text: root.current_time
            font_size: '18sp'
            bold: True

<DetectionCard>:
    canvas.before:
        Color:
            rgba: 0.2, 0.2, 0.2, 1 if not root.is_alert else 0.4, 0.1, 0.1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [5]
    
    BoxLayout:
        padding: '8dp'
        spacing: '5dp'
        
        Label:
            text: root.timestamp
            size_hint_x: 0.15
            font_size: '12sp'
        
        Label:
            text: root.plate_number
            size_hint_x: 0.2
            font_size: '16sp'
            bold: True
        
        Label:
            text: f"{root.make} {root.model}"
            size_hint_x: 0.35
            font_size: '14sp'
        
        Label:
            text: root.colour
            size_hint_x: 0.15
        
        StatusIcon:
            icon: root.status_icon
            color: root.status_color
            size_hint_x: 0.15
```

---

## Cost Model (Final)

### Monthly Costs (8 hours driving/day, 30 days)

| Component | Usage | Monthly Cost (AUD) |
|-----------|-------|-------------------|
| **Hot Path** | | |
| Alert Worker | 500 events/day × 30 | $0.20 |
| KV operations | 2,000/day × 30 | $0.70 |
| D1 writes/reads | 5,000/day × 30 | $1.00 |
| Durable Objects | Dashboard WebSocket | $3.00 |
| **Rego Path** | | |
| NEVDIS API (MotorWeb) | 100 plates/day × $0.25 × 30 | **$75.00** |
| Rego Worker | 100/day × 30 | $0.05 |
| **Face Path** | | |
| Local processing | On-device (Hailo) | $0.00 |
| Vectorize (fleet sync) | 1,000 embeddings | $0.15 |
| **Cold Path** | | |
| R2 storage | 100GB (TeslaCam + Pi) | $1.50 |
| Stream transcode | 480 min/day × 30 | $36.00 |
| Workers AI (batch) | Scene summaries | $2.00 |
| Workers AI (STT) | 120 min/day × 30 | $5.00 |
| Workflows | ~100 runs/month | $0.50 |
| **LTE Data** | ~5GB/month | $15.00 |
| **TOTAL** | | **~$140 AUD/month** |

### Cost Optimization Options

| Optimization | Savings | Trade-off |
|--------------|---------|-----------|
| Reduce NEVDIS to 50 plates/day | -$37.50 | Miss some rego lookups |
| Skip cloud STT (local Whisper) | -$5.00 | Slower, less accurate |
| WiFi-only upload (no LTE) | -$15.00 | No real-time alerts |
| Local-only face matching | -$0.15 | No fleet-wide alerts |

**Optimized total: ~$80 AUD/month**

---

## Implementation Phases

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1** | Week 1 | Pi 5 setup, USB gadget mode, TeslaCam integration |
| **Phase 2** | Week 2 | Hailo-8L setup, YOLO + plate detector models |
| **Phase 3** | Week 3 | LPRNet OCR, NEVDIS API integration |
| **Phase 4** | Week 4 | Dashboard UI (Kivy), real-time display |
| **Phase 5** | Week 5 | Face detection + ArcFace embedding (on-device) |
| **Phase 6** | Week 6 | Cloud integration: Workers, D1, R2 |
| **Phase 7** | Week 7 | Cold path: Workflow, Stream, batch processing |
| **Phase 8** | Week 8 | Watchlist alerts, fleet dashboard |
| **Phase 9** | Week 9 | Testing, optimization, enclosure |
| **Phase 10** | Week 10 | Documentation, deployment |

---

## Summary

This architecture provides:

1. **Tesla Integration** via USB gadget mode — Pi appears as standard TeslaCam USB drive
2. **Dual Camera System** — Tesla's 8 cameras + independent Pi camera
3. **On-Device AI** via Hailo-8L — plates, faces, objects at 16+ FPS
4. **Australian Rego Lookups** via NEVDIS — make/model/color/stolen/WOVR
5. **Real-Time Watchlist Alerts** — stolen vehicles, custom fleet tracking
6. **Privacy-First Face Recognition** — all processing on-device, only embeddings to cloud
7. **5" Touch Dashboard** — live stats, recent detections, alerts

**Total hardware cost: ~$590 AUD**
**Monthly operating cost: ~$140 AUD** (or ~$80 AUD optimized)
