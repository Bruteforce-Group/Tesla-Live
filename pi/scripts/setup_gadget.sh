#!/bin/bash
set -e

echo "=== Tesla USB Gadget Mode Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Configuration
TESLACAM_SIZE="${TESLACAM_SIZE:-200G}"
DATA_DIR="/data"
TESLACAM_IMG="$DATA_DIR/teslacam.img"

# 1. Enable USB gadget mode in boot config
echo "Configuring boot parameters..."

# Add dtoverlay for dwc2
if ! grep -q "dtoverlay=dwc2" /boot/firmware/config.txt; then
    echo "dtoverlay=dwc2,dr_mode=peripheral" >> /boot/firmware/config.txt
fi

# Add modules to cmdline
if ! grep -q "modules-load=dwc2,g_mass_storage" /boot/firmware/cmdline.txt; then
    sed -i 's/$/ modules-load=dwc2,g_mass_storage/' /boot/firmware/cmdline.txt
fi

# 2. Create data directory
echo "Creating data directory..."
mkdir -p $DATA_DIR

# 3. Create TeslaCam disk image
echo "Creating TeslaCam disk image ($TESLACAM_SIZE)..."
if [ ! -f "$TESLACAM_IMG" ]; then
    truncate -s $TESLACAM_SIZE $TESLACAM_IMG
    mkfs.exfat -n TeslaCam $TESLACAM_IMG
    
    # Mount temporarily to create folder structure
    TEMP_MOUNT=$(mktemp -d)
    mount -o loop $TESLACAM_IMG $TEMP_MOUNT
    mkdir -p $TEMP_MOUNT/TeslaCam/RecentClips
    mkdir -p $TEMP_MOUNT/TeslaCam/SavedClips
    mkdir -p $TEMP_MOUNT/TeslaCam/SentryClips
    umount $TEMP_MOUNT
    rmdir $TEMP_MOUNT
fi

# 4. Create systemd service for gadget mode
echo "Creating systemd service..."
cat > /etc/systemd/system/teslacam-gadget.service << 'EOF'
[Unit]
Description=TeslaCam USB Gadget Mode
After=local-fs.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/teslacam-gadget.sh start
ExecStop=/usr/local/bin/teslacam-gadget.sh stop

[Install]
WantedBy=multi-user.target
EOF

# 5. Create gadget control script
cat > /usr/local/bin/teslacam-gadget.sh << 'SCRIPT'
#!/bin/bash

TESLACAM_IMG="/data/teslacam.img"
MOUNT_POINT="/mnt/teslacam"

start() {
    echo "Starting TeslaCam gadget..."
    
    # Create mount point
    mkdir -p $MOUNT_POINT
    
    # Set up loop device
    LOOP_DEV=$(losetup -f --show $TESLACAM_IMG)
    echo $LOOP_DEV > /run/teslacam-loop
    
    # Mount for Pi read access
    mount -o ro $LOOP_DEV $MOUNT_POINT
    
    # Load USB gadget
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
        iSerialNumber="TESLA001"
    
    echo "TeslaCam gadget started on $LOOP_DEV"
}

stop() {
    echo "Stopping TeslaCam gadget..."
    
    # Unload gadget
    modprobe -r g_mass_storage
    
    # Unmount
    umount $MOUNT_POINT 2>/dev/null || true
    
    # Release loop device
    if [ -f /run/teslacam-loop ]; then
        LOOP_DEV=$(cat /run/teslacam-loop)
        losetup -d $LOOP_DEV 2>/dev/null || true
        rm /run/teslacam-loop
    fi
    
    echo "TeslaCam gadget stopped"
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
SCRIPT

chmod +x /usr/local/bin/teslacam-gadget.sh

# 6. Enable service
systemctl daemon-reload
systemctl enable teslacam-gadget.service

echo ""
echo "=== Setup Complete ==="
echo "Reboot required for changes to take effect."
echo "After reboot, the Pi will appear as a USB drive to the Tesla."
echo ""
echo "Run: sudo reboot"
