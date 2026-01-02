#!/bin/bash
set -e

SERVICE_NAME="tesla-dashcam"
APP_DIR="/opt/tesla-dashcam"

echo "=== Installing systemd service (${SERVICE_NAME}) ==="

sudo mkdir -p $APP_DIR
sudo cp -r "$(pwd)"/* $APP_DIR

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
