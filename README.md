# Smart Classroom Lighting Control System

Control 8 classroom lights wirelessly using Raspberry Pi 5 and 8-channel relay module with mobile-responsive web dashboard.

## Quick Start (Raspberry Pi 5)

```bash
# Install
chmod +x scripts/install.sh
./scripts/install.sh

# Access dashboard
http://raspberrypi.local:5000
Login: admin / classroom123
```

## Hardware Connections

| Relay | GPIO (BCM) | Physical Pin |
|-------|-----------|-------------|
| IN1   | GPIO 17   | Pin 11      |
| IN2   | GPIO 12   | Pin 32      |
| IN3   | GPIO 27   | Pin 13      |
| IN4   | GPIO 22   | Pin 15      |
| IN5   | GPIO 23   | Pin 16      |
| IN6   | GPIO 24   | Pin 18      |
| IN7   | GPIO 25   | Pin 22      |
| IN8   | GPIO 5    | Pin 29      |
| VCC   | 5V        | Pin 2       |
| GND   | GND       | Pin 6       |

**10 wires total** - 8 GPIO + VCC + GND

## Configuration

Edit `.env` to change:
- `USERNAME` and `PASSWORD` (default: admin/classroom123)
- `SECRET_KEY` (IMPORTANT: Change for production!)
- `PORT` (default: 5000)

## Service Management

```bash
sudo systemctl status smart-classroom  # Check status
sudo systemctl restart smart-classroom # Restart
sudo journalctl -u smart-classroom -f  # View logs
```

## API Endpoints

```bash
GET  /api/status          # Get all relay states
POST /api/relay/1/on      # Turn ON relay 1
POST /api/relay/1/off     # Turn OFF relay 1
POST /api/relay/1/toggle  # Toggle relay 1
POST /api/relay/all/on    # All ON
POST /api/relay/all/off   # All OFF
```

## Project Structure

```
app/              - Flask web application
api/              - REST API routes
config/           - Configuration files
hardware/         - GPIO relay controllers
scripts/          - Installation scripts
requirements.txt  - Python dependencies
```

**Built for Raspberry Pi 5 with lgpio**
