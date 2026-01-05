-- Trips table
CREATE TABLE IF NOT EXISTS trips (
    trip_id TEXT PRIMARY KEY,
    vehicle_id TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    start_gps_lat REAL,
    start_gps_lng REAL,
    end_gps_lat REAL,
    end_gps_lng REAL,
    distance_km REAL,
    status TEXT DEFAULT 'recording',
    stream_uid TEXT,
    teslacam_clips INTEGER DEFAULT 0,
    pi_clips INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Events table (alerts, incidents)
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    trip_id TEXT REFERENCES trips(trip_id),
    vehicle_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT,
    object_type TEXT,
    bbox_x REAL,
    bbox_y REAL,
    bbox_width REAL,
    bbox_height REAL,
    attributes TEXT, -- JSON string of attributes (vehicle colour/type, clothing, species)
    audio_label TEXT,
    audio_confidence REAL,
    embedding_vector_id TEXT,
    timestamp DATETIME NOT NULL,
    gps_lat REAL,
    gps_lng REAL,
    speed_kmh REAL,
    confidence REAL,
    clip_uid TEXT,
    scene_description TEXT,
    processed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_trip ON events(trip_id, timestamp);
CREATE INDEX idx_events_type ON events(event_type, timestamp);
CREATE INDEX idx_events_audio ON events(audio_label, timestamp) WHERE audio_label IS NOT NULL;

-- Plate sightings
CREATE TABLE IF NOT EXISTS plate_sightings (
    sighting_id TEXT PRIMARY KEY,
    trip_id TEXT REFERENCES trips(trip_id),
    vehicle_id TEXT NOT NULL,
    plate_number TEXT NOT NULL,
    plate_state TEXT,
    confidence REAL,
    timestamp DATETIME NOT NULL,
    gps_lat REAL,
    gps_lng REAL,
    
    -- NEVDIS data
    rego_status TEXT,
    rego_expiry DATE,
    vehicle_make TEXT,
    vehicle_model TEXT,
    vehicle_year INTEGER,
    vehicle_colour TEXT,
    vin TEXT,
    
    -- Flags
    stolen_flag BOOLEAN DEFAULT FALSE,
    stolen_jurisdiction TEXT,
    stolen_date DATE,
    wovr_status TEXT,
    wovr_type TEXT,
    ppsr_encumbered BOOLEAN DEFAULT FALSE,
    
    -- Watchlist
    watchlist_hit TEXT,
    watchlist_priority TEXT,
    
    linked_event_id TEXT REFERENCES events(event_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plates_number ON plate_sightings(plate_number);
CREATE INDEX idx_plates_trip ON plate_sightings(trip_id, timestamp);
CREATE INDEX idx_plates_watchlist ON plate_sightings(watchlist_hit) WHERE watchlist_hit IS NOT NULL;

-- Plate watchlist
CREATE TABLE IF NOT EXISTS plate_watchlist (
    plate_number TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    notes TEXT,
    added_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Face sightings (metadata only, no images)
CREATE TABLE IF NOT EXISTS face_sightings (
    sighting_id TEXT PRIMARY KEY,
    trip_id TEXT REFERENCES trips(trip_id),
    vehicle_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    gps_lat REAL,
    gps_lng REAL,
    bbox_x REAL,
    bbox_y REAL,
    bbox_width REAL,
    bbox_height REAL,
    detection_confidence REAL,
    matched_face_id TEXT,
    match_confidence REAL,
    linked_event_id TEXT REFERENCES events(event_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_faces_matched ON face_sightings(matched_face_id) WHERE matched_face_id IS NOT NULL;

-- Audio events (edge-captured)
CREATE TABLE IF NOT EXISTS audio_events (
    event_id TEXT PRIMARY KEY,
    trip_id TEXT REFERENCES trips(trip_id),
    vehicle_id TEXT NOT NULL,
    label TEXT NOT NULL,
    confidence REAL,
    rms REAL,
    timestamp DATETIME NOT NULL,
    gps_lat REAL,
    gps_lng REAL,
    linked_event_id TEXT REFERENCES events(event_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audio_events_label ON audio_events(label, timestamp);

-- Enrolled faces (for matching)
CREATE TABLE IF NOT EXISTS enrolled_faces (
    face_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'driver',
    notes TEXT,
    vehicle_id TEXT,
    embedding_vector_id TEXT,
    enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Watchlist alerts log
CREATE TABLE IF NOT EXISTS watchlist_alerts (
    alert_id TEXT PRIMARY KEY,
    plate_number TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    vehicle_make TEXT,
    vehicle_model TEXT,
    vehicle_colour TEXT,
    gps_lat REAL,
    gps_lng REAL,
    timestamp DATETIME NOT NULL,
    details TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by TEXT,
    acknowledged_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_unack ON watchlist_alerts(acknowledged, timestamp) WHERE acknowledged = FALSE;

-- Footage index
CREATE TABLE IF NOT EXISTS footage (
    footage_id TEXT PRIMARY KEY,
    trip_id TEXT REFERENCES trips(trip_id),
    vehicle_id TEXT NOT NULL,
    source TEXT NOT NULL,
    r2_key TEXT NOT NULL,
    stream_uid TEXT,
    duration_seconds REAL,
    file_size_bytes INTEGER,
    captured_at DATETIME NOT NULL,
    uploaded_at DATETIME,
    processed_at DATETIME,
    processing_status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_footage_trip ON footage(trip_id, captured_at);
CREATE INDEX idx_footage_status ON footage(processing_status);
