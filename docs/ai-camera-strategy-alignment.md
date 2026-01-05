# AI Camera Strategy Alignment

This document maps the provided Object Detection Strategy (`file://Object%20detection%20strategy.pdf`) to the Tesla Live stack (Pi on-device pipeline + Cloudflare backend + optional React dashboard). It is the single source for how we implement detection, masking, audio, metadata, and testing across tiers.

## Scope and Tiers
- **Standard (edge-first):** On-device YOLOv8-n/PP-YOLOE on Hailo, masking for faces/plates, plate OCR, watchlist alerts, minimal audio (siren/alarm).
- **Enhanced:** Add attribute classifiers (vehicle type/colour, human accessories), audio events (glass break, bark, horn), better tracking (DeepSORT/ByteTrack).
- **Centralized:** Cross-camera search, make/model recognition, species classifiers, natural-language and vector search via Cloudflare (D1 + Vectorize).

## Model Selection and Training
- **Detectors:** Anchor-free YOLOv8-n (default) or PP-YOLOE; for fisheye, prefer fisheye-aware models (FisheyeDetNet/PGDS-YOLOv8s) or apply calibrated equirectangular undistortion per camera.
- **Classifiers:** Faces (MobileFaceNet/ArcFace-lite), license plates (detector + LPRNet/CRNN), vehicle attributes (type/colour; make/model for centralized), human attributes (multi-task gender/clothing/accessories), animal species (SpeciesNet/Wildlife Insights AI + local pets).
- **Audio:** YAMNet/VGGish or vendor models (Sensory SoundID). Use 16–32 kHz capture, log-Mel (40–64 bands), z-score normalize.
- **Optimization:** Prune/quantize (FP16/INT8) and benchmark on Pi + Hailo; keep per-model latency budgets to sustain ≥16 FPS.

## Dynamic Masking Rules
- Inflate detection boxes 30–50%; for instance masks, dilate. Always mask faces and plates heavily (prefer pixelation for plates).
- Children/animals: full-body masks with min size; extend to limbs/tails.
- Tracking: DeepSORT/ByteTrack with Kalman smoothing; persist masks briefly after occlusion.
- Dwell/loiter: when flagged, broaden mask to surrounding area.
- Fisheye: apply masks in distorted space or project mask/image via calibrated equirectangular transforms.

## Audio Integration
- Capture at 16/32 kHz → pre-emphasis → log-Mel. Run on-device classifier; drop raw audio after inference.
- Report events with timestamp, camera ID, class, confidence; correlate with visual detections (e.g., siren near vehicle).
- Support custom enrolment (8–10 s sample → embedding → similarity threshold).

## Metadata, Storage, and Search
- Event record fields: object_id, type, bbox, score, attributes (vehicle type/colour/make/model; human clothing/accessories; animal species), audio labels, timestamps (start/end), camera_id, dwell/line-cross flags, embeddings (face/CLIP/text).
- Storage: time-series or D1 tables for events/trips/faces/plates; vector search via Cloudflare Vectorize (or Milvus/Elasticsearch if centralized).
- Search UX: structured filters + vector search for free-text (“red sedan near horn”); blur thumbnails and enforce access controls.

## Testing and Deployment
- Unit tests per module (detectors, masks, audio, OCR); integration tests for detection → masking → metadata → search; regression suite for latency/accuracy.
- Performance: benchmark per hardware class; include stress tests (crowds/traffic), network drop tolerance, and fisheye/undistorted cases.
- Rollout: feature flags per tier (Standard → Enhanced → Centralized); monitor FP/FN rates and retrain as needed.

## Privacy, Compliance, and Governance
- Perform DPIA; document data flows, retention, and deletion. Encrypt in transit/at rest; restrict and audit access.
- Policies: when masking applies, override rules, audio handling, retention windows. Support data-subject requests.
- User/operator guides: calibration (including fisheye), mic setup, adjusting mask margins, sample natural-language searches.

## Action Items (project-specific)
- [ ] Benchmark YOLOv8-n + fisheye option on Pi/Hailo; choose default per camera profile.
- [ ] Wire mask inflation/smoothing in `pi/core/detector.py` and `ui` display; add pixelation option for plates/faces.
- [ ] Add audio pipeline (log-Mel + YAMNet/VGGish) and event publication into existing alert flow.
- [ ] Extend metadata schema and Cloudflare Vectorize index for embeddings + hybrid search.
- [ ] Add regression/perf tests covering detection→masking→search; include fisheye fixtures.
