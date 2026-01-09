#!/bin/bash

# Btrfs Management Web Tool Setup Script
# This script installs and configures the web tool for managing Btrfs filesystems and Snapper snapshots

set -e

# Configuration
WEB_TOOL_DIR="/opt/btrfs-manager"
USER="root"
PORT="8787"

echo "Setting up Btrfs Management Web Tool..."

# Create the target directory
sudo mkdir -p "$WEB_TOOL_DIR"
sudo chown "$USER":"$USER" "$WEB_TOOL_DIR"

# Install required packages (for openSUSE)
if command -v zypper &> /dev/null; then
    echo "Installing required packages..."
    sudo zypper install -y python3 python3-pip python3-flask btrfsprogs snapper python3-psutil
elif command -v apt-get &> /dev/null; then
    echo "Installing required packages..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-flask btrfs-tools snapper python3-psutil
elif command -v yum &> /dev/null; then
    echo "Installing required packages..."
    sudo yum install -y python3 python3-pip python3-flask btrfs-progs snapper python3-psutil
fi

# Copy application files
sudo cp -r "$PWD/src" "$WEB_TOOL_DIR/"
sudo cp -r "$PWD/systemd" "$WEB_TOOL_DIR/"
sudo cp "$PWD/btrfs-manager.py" "$WEB_TOOL_DIR/"

# Create web user and set permissions
sudo useradd -r -s /bin/false btrfs-web 2>/dev/null || true

# Create systemd service file
sudo tee "/etc/systemd/system/btrfs-manager.service" > /dev/null <<EOF
[Unit]
Description=Btrfs Management Web Tool
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$WEB_TOOL_DIR
ExecStart=/usr/bin/python3 $WEB_TOOL_DIR/btrfs-manager.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable btrfs-manager
sudo systemctl start btrfs-manager

echo "Setup complete!"
echo "Btrfs Management Web Tool is now running on port $PORT"
echo "Access it at: http://localhost:$PORT"
echo ""
echo "To check service status: sudo systemctl status btrfs-manager"
echo "To view logs: sudo journalctl -u btrfs-manager -f"