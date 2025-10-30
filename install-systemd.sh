#!/bin/bash

# MediaLive Distributor - Systemd Installation Script
# This script installs the application as a systemd service (alternative to Docker)

set -e

echo "=== MediaLive Distributor Installation ==="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv ffmpeg

# Create application user
echo "Creating application user..."
if ! id "medialive" &>/dev/null; then
    useradd -r -s /bin/false medialive
fi

# Create installation directory
INSTALL_DIR="/opt/medialive-distributor"
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/config
mkdir -p $INSTALL_DIR/logs
mkdir -p $INSTALL_DIR/static

# Copy application files
echo "Copying application files..."
cp app.py $INSTALL_DIR/
cp requirements.txt $INSTALL_DIR/
cp -r static/* $INSTALL_DIR/static/

# Create virtual environment
echo "Creating Python virtual environment..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set permissions
echo "Setting permissions..."
chown -R medialive:medialive $INSTALL_DIR

# Install systemd service
echo "Installing systemd service..."
cp systemd/medialive-distributor.service /etc/systemd/system/
systemctl daemon-reload

# Enable and start service
echo "Enabling service..."
systemctl enable medialive-distributor.service

echo
echo "=== Installation Complete ==="
echo
echo "To start the service:"
echo "  sudo systemctl start medialive-distributor"
echo
echo "To check status:"
echo "  sudo systemctl status medialive-distributor"
echo
echo "To view logs:"
echo "  sudo journalctl -u medialive-distributor -f"
echo
echo "Web interface will be available at: http://localhost:8000"
echo
