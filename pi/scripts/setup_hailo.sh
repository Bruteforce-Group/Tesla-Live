#!/bin/bash
set -e

echo "=== Hailo Runtime Setup for Pi 5 ==="

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    echo "Error: This script requires 64-bit ARM (aarch64)"
    exit 1
fi

# Add Hailo APT repository
echo "Adding Hailo repository..."
curl -fsSL https://hailo.ai/hailo-rpi5/hailo-rpi5.pub | sudo gpg --dearmor -o /usr/share/keyrings/hailo-rpi5.gpg
echo "deb [signed-by=/usr/share/keyrings/hailo-rpi5.gpg] https://hailo.ai/hailo-rpi5/ bookworm main" | \
    sudo tee /etc/apt/sources.list.d/hailo-rpi5.list

# Update and install
echo "Installing Hailo runtime..."
sudo apt update
sudo apt install -y hailo-all

# Verify installation
echo "Verifying Hailo installation..."
hailortcli fw-control identify

echo ""
echo "=== Hailo Setup Complete ==="
echo "Hailo-8L should now be accessible."
