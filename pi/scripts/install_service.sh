#!/bin/bash
set -e

SERVICE_NAME="tesla-dashcam"
APP_DIR="${APP_DIR:-/home/danielborrowman/tesla-dashcam}"

echo "=== Installing systemd service (${SERVICE_NAME}) to ${APP_DIR} ==="

sudo mkdir -p "$APP_DIR"

SRC_DIR="$(pwd)"
if [ "$(realpath "$SRC_DIR")" != "$(realpath "$APP_DIR")" ]; then
  sudo cp -a "$SRC_DIR"/. "$APP_DIR"/
else
  echo "Source and destination are the same; skipping copy."
fi

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Tesla Dashcam AI
After=network-online.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}/pi
ExecStart=/usr/bin/python3 ${APP_DIR}/pi/main.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl restart ${SERVICE_NAME}.service

echo "Service installed and started."
