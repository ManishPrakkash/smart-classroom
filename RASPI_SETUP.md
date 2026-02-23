# Raspberry Pi Setup Guide - Smart Classroom

> **Supported Models:** Raspberry Pi 3, 4, 5  
> **Camera Support:** Camera Module 3, Camera Module 2, USB Webcams

## Raspberry Pi 5 with Camera Module 3

For **Raspberry Pi 5** users, the setup script automatically detects your hardware and installs **lgpio** instead of pigpio. Camera Module 3 is fully supported via `picamera2`.

### Quick Start (RPi 5 + Camera Module 3)

1. **Clone the repository:**
   ```bash
   cd ~
   git clone <your-repo-url> smart-classroom
   cd smart-classroom/backend
   ```

2. **Run the startup script:**
   ```bash
   chmod +x start_backend.sh
   ./start_backend.sh
   ```

The script will automatically:
- Detect Raspberry Pi 5 and install `lgpio`
- Detect Camera Module 3 and configure `picamera2`
- Install all required dependencies
- Start the backend server

### Verify Camera Module 3

```bash
libcamera-hello --list-cameras
```

You should see output like:
```
Available cameras
-----------------
0 : imx708 [4608x2592] (/base/axi/pcie@120000/rp1/i2c@80000/imx708@1a)
```

---

## Manual Setup (All Models)

### 1. Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python & GPIO Dependencies

**For Raspberry Pi 3/4:**
```bash
sudo apt install python3 python3-pip python3-venv -y
sudo apt install pigpio python3-pigpio -y
```

**For Raspberry Pi 5:**
```bash
sudo apt install python3 python3-pip python3-venv -y
sudo apt install python3-lgpio -y
```

**Enable pigpio daemon (RPi 3/4 only):**
```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

**Add user to GPIO group:**
```bash
sudo usermod -a -G gpio $USER
# Logout and login again for group changes to take effect
```

**Install Camera Support (if using Pi Camera Module):**
```bash
sudo apt install python3-picamera2 python3-libcamera -y
```

### 3. Create Project Directory
```bash
mkdir -p ~/smart-classroom/backend
cd ~/smart-classroom/backend
```

### 4. Create Virtual Environment
```bash
python3 -m venv venv
```

### 5. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 6. Install Dependencies

**Option A: Using requirements.txt** (Recommended)

Transfer the `requirements.txt` file to your Pi, then:
```bash
pip install -r requirements.txt
```

**Option B: Manual Install**
```bash
pip install flask flask-cors gpiozero
```

### 7. Copy Backend Files

Transfer these files to `~/smart-classroom/backend/`:
- `app.py`
- `devices.py`
- `requirements.txt`

**Using SCP from your computer:**
```bash
scp app.py devices.py requirements.txt pi@10.27.253.96:~/smart-classroom/backend/
```

### 8. Run the Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the Flask server
python app.py
```

The server will start on `http://10.27.253.96:5000`

---

## Auto-Start on Boot (Optional)

### Create Systemd Service

1. **Create service file:**
```bash
sudo nano /etc/systemd/system/smartclassroom.service
```

2. **Add this content:**
```ini
[Unit]
Description=Smart Classroom Flask Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart-classroom/backend
Environment="PATH=/home/pi/smart-classroom/backend/venv/bin"
ExecStart=/home/pi/smart-classroom/backend/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartclassroom.service
sudo systemctl start smartclassroom.service
```

4. **Check status:**
```bash
sudo systemctl status smartclassroom.service
```

5. **View logs:**
```bash
sudo journalctl -u smartclassroom.service -f
```

---

## Complete Script (Copy & Paste)

```bash
#!/bin/bash

# Smart Classroom Setup Script for Raspberry Pi

echo "🚀 Setting up Smart Classroom..."

# Update system
echo "📦 Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python..."
sudo apt install python3 python3-pip python3-venv -y

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/smart-classroom/backend
cd ~/smart-classroom/backend

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install flask flask-cors gpiozero

echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Transfer app.py and devices.py to ~/smart-classroom/backend/"
echo "2. Activate venv: source ~/smart-classroom/backend/venv/bin/activate"
echo "3. Run server: python app.py"
echo ""
echo "Server will be available at: http://10.27.253.96:5000"
```

**To use this script:**
1. Save as `setup.sh` on your Pi
2. Make executable: `chmod +x setup.sh`
3. Run: `./setup.sh`

---

## Quick Reference

### Daily Usage

```bash
# Navigate to project
cd ~/smart-classroom/backend

# Activate virtual environment
source venv/bin/activate

# Run server
python app.py

# Deactivate virtual environment (when done)
deactivate
```

### Troubleshooting

**Check if server is running:**
```bash
curl http://localhost:5000/status
```

**Check which process is using port 5000:**
```bash
sudo lsof -i :5000
```

**Kill process on port 5000:**
```bash
sudo kill -9 $(sudo lsof -t -i:5000)
```

**View GPIO permissions (if needed):**
```bash
groups
sudo usermod -a -G gpio pi
```

---

## File Transfer Methods

### Method 1: SCP (from your computer)
```bash
scp app.py devices.py requirements.txt pi@10.27.253.96:~/smart-classroom/backend/
```

### Method 2: Git Clone (if using Git)
```bash
cd ~/smart-classroom
git clone <your-repo-url> backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Method 3: WinSCP / FileZilla
- Use GUI file transfer tools
- Connect to `10.27.253.96`
- Transfer files to `/home/pi/smart-classroom/backend/`

---

## Testing

### Test Flask Server
```bash
# From another terminal on Pi
curl http://localhost:5000/status

# Check devices endpoint
curl http://localhost:5000/devices

# Test device control
curl http://localhost:5000/control/light1/on
curl http://localhost:5000/control/light1/off
```

### Test from Mobile/Computer
- Ensure on same WiFi network
- Visit: `http://10.27.253.96:5000/status`
- Or use the mobile app!

---

## Troubleshooting

### Slow Network / piwheels Timeout

If you see errors like `ReadTimeoutError` when installing packages from piwheels:

**Solution 1: The startup script handles this automatically** (recommended)
```bash
# Just run the script - it has built-in retry logic and extended timeouts
./start_backend.sh
```

**Solution 2: Manual pip configuration** (if needed)
```bash
# Create pip config file with longer timeouts
mkdir -p ~/.config/pip
cat > ~/.config/pip/pip.conf << EOF
[global]
timeout = 100
retries = 5
EOF

# Then retry installation
pip install -r requirements.txt
```

**Solution 3: Install dependencies one by one** (for very slow connections)
```bash
# Install critical packages first
pip install flask flask-cors --timeout 200
pip install gpiozero pigpio --timeout 200
pip install apscheduler pytz ntplib --timeout 200
pip install firebase-admin --timeout 200
```

### Camera Not Detected

```bash
# Check camera connection
libcamera-hello --list-cameras

# If camera not found, check ribbon cable connection
# Ensure camera is enabled in raspi-config:
sudo raspi-config
# Navigate to: Interface Options -> Camera -> Enable
```

### GPIO Permissions Error

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout and login again, or reboot
sudo reboot
```

### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill <PID>

# Or use a different port by editing app.py
```

---

## Summary

✅ Install Python 3 and pip  
✅ Create virtual environment  
✅ Install dependencies (flask, flask-cors, gpiozero)  
✅ Transfer backend files  
✅ Run the server  
✅ Optional: Auto-start on boot  

Your Raspberry Pi is ready to control the classroom! 🎓⚡
