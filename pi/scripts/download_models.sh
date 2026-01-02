#!/bin/bash
set -e

MODELS_DIR="/opt/dashcam/models"
mkdir -p $MODELS_DIR
cd $MODELS_DIR

echo "=== Downloading Hailo Models ==="

# YOLOv8-Nano (pre-compiled for Hailo-8L)
echo "Downloading YOLOv8-Nano..."
wget -q --show-progress \
    "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/yolov8n.hef" \
    -O yolov8n.hef

# RetinaFace for face detection
echo "Downloading RetinaFace..."
wget -q --show-progress \
    "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/retinaface_mobilenet_v1.hef" \
    -O retinaface.hef

# ArcFace for face embedding
echo "Downloading ArcFace..."
wget -q --show-progress \
    "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/arcface_mobilefacenet.hef" \
    -O arcface.hef

# LPRNet for license plate OCR (may need custom training for AU plates)
echo "Downloading LPRNet..."
wget -q --show-progress \
    "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/lprnet.hef" \
    -O lprnet.hef

# License plate detector (YOLO-based)
echo "Downloading Plate Detector..."
wget -q --show-progress \
    "https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.11.0/hailo8l/tiny_yolov4_license_plates.hef" \
    -O plate_detector.hef

echo ""
echo "=== Models Downloaded ==="
ls -lh $MODELS_DIR
