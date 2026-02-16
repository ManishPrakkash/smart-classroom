# Raspberry Pi 5 Deployment Guide

## Step 1: On Your Windows PC (Already Done)

✅ Code is ready in `C:\smart-classroom`

## Step 2: Push to GitHub

```bash
cd C:\smart-classroom
git add .
git commit -m "Smart Classroom Lighting Control System - Production Ready"
git push origin main
```

## Step 3: On Raspberry Pi 5

### A. Clone Repository

```bash
cd ~
git clone https://github.com/ManishPrakkash/smart-classroom.git
cd smart-classroom
```

### B. Run Installation

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

This will:
- Install dependencies (Flask, lgpio)
- Create virtual environment
- Setup .env configuration
- Configure GPIO permissions

### C. Setup Auto-Start Service

```bash
chmod +x scripts/setup_service.sh
./scripts/setup_service.sh
```

### D. Connect Hardware

**10 Wire Connections:**

| From Relay | To Raspberry Pi | Pin Number |
|------------|----------------|------------|
| VCC        | 5V             | Pin 2      |
| GND        | GND            | Pin 6      |
| IN1        | GPIO 17        | Pin 11     |
| IN2        | GPIO 27        | Pin 13     |
| IN3        | GPIO 22        | Pin 15     |
| IN4        | GPIO 23        | Pin 16     |
| IN5        | GPIO 24        | Pin 18     |
| IN6        | GPIO 25        | Pin 22     |
| IN7        | GPIO 5         | Pin 29     |
| IN8        | GPIO 6         | Pin 31     |

### E. Access Dashboard

1. Find Pi IP address: `hostname -I`
2. Open browser: `http://YOUR_PI_IP:5000`
3. Login: `admin` / `classroom123`

## Step 4: Change Default Password

```bash
cd ~/smart-classroom
nano .env
```

Change:
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=classroom123
```

Restart:
```bash
sudo systemctl restart smart-classroom
```

## Service Commands

```bash
# Check status
sudo systemctl status smart-classroom

# Restart
sudo systemctl restart smart-classroom

# Stop
sudo systemctl stop smart-classroom

# Start
sudo systemctl start smart-classroom

# View logs
sudo journalctl -u smart-classroom -f
```

## Testing Without Lights

```bash
cd ~/smart-classroom/scripts
python3 test_relays.py
```

This will click all 8 relays on and off - you should hear clicking sounds.

## Network Access

The dashboard is accessible from:
- Raspberry Pi: `http://localhost:5000`
- Same WiFi: `http://raspberrypi.local:5000`
- IP Address: `http://192.168.X.X:5000`

## Troubleshooting

### Error: "lgpio not found"
```bash
sudo apt install python3-lgpio
```

### Error: "Permission denied"
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

### Check if service is running
```bash
sudo systemctl status smart-classroom
```

### View error logs
```bash
cat ~/smart-classroom/logs/smart_classroom.log
```

## Project Files

```
smart-classroom/
├── app/              # Flask web application
├── api/              # REST API routes
├── config/           # Configuration
├── hardware/         # GPIO controller
├── scripts/          # Install & service scripts
├── .env              # Credentials (change password!)
└── requirements.txt  # Python dependencies
```

**System is production-ready!** 🚀
