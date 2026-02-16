#!/bin/bash
# Setup systemd service for Smart Classroom

set -e

SERVICE_NAME="smart-classroom"
PROJECT_DIR="$HOME/smart-classroom"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "======================================"
echo "Smart Classroom Service Setup"
echo "======================================"
echo ""

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ Virtual environment not found. Run install.sh first."
    exit 1
fi

# Create service file
echo "📝 Creating systemd service file..."

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Smart Classroom Lighting Control System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/app/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service
echo "✅ Enabling service to start on boot..."
sudo systemctl enable "$SERVICE_NAME.service"

# Start service
echo "▶️  Starting service..."
sudo systemctl start "$SERVICE_NAME.service"

# Wait a moment for service to start
sleep 2

# Check status
echo ""
echo "======================================"
echo "Service Status"
echo "======================================"
sudo systemctl status "$SERVICE_NAME.service" --no-pager

echo ""
echo "======================================"
echo "✅ Service Setup Complete!"
echo "======================================"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Web interface available at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
