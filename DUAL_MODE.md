# Dual Environment Setup

This project automatically detects the environment and uses the appropriate controller:

## 🪟 **Windows PC Testing (Mock Mode)**

### Quick Start:
```bash
# Double-click this file:
test_windows.bat

# OR manually:
python -m venv venv
venv\Scripts\activate
pip install Flask Werkzeug python-dotenv
python app\app.py
```

**What happens:**
- ✅ Automatically detects NO lgpio available
- ✅ Uses `MockRelayController` for simulation
- ✅ Web interface works perfectly
- ✅ Relay clicks are logged (no actual hardware)
- ✅ Test all features before deploying to Pi

**Access:** http://localhost:5000

---

## 🍓 **Raspberry Pi 5 (Hardware Mode)**

### Installation:
```bash
cd ~
git clone https://github.com/ManishPrakkash/smart-classroom.git
cd smart-classroom
chmod +x scripts/install.sh
./scripts/install.sh
```

**What happens:**
- ✅ Installs lgpio system library
- ✅ Automatically detects lgpio available
- ✅ Uses `RelayController` for real GPIO control
- ✅ Controls actual relay hardware
- ✅ Auto-starts on boot

**Access:** http://raspberrypi.local:5000

---

## 🔄 **How Auto-Detection Works**

**app.py automatically:**
1. Tries to import `lgpio`
2. **If successful** → Uses `RelayController` (real hardware)
3. **If fails** → Uses `MockRelayController` (simulation)
4. **Zero configuration needed!**

```python
try:
    import lgpio
    from hardware.relay_controller import RelayController
    MOCK_MODE = False
except ImportError:
    from hardware.mock_relay_controller import MockRelayController as RelayController
    MOCK_MODE = True
```

---

## 📋 **File Structure**

```
smart-classroom/
├── hardware/
│   ├── relay_controller.py       # Real GPIO (Pi only)
│   └── mock_relay_controller.py  # Simulation (Windows/Mac)
├── app/app.py                     # Auto-detects mode
├── test_windows.bat               # Quick Windows test
└── scripts/install.sh             # Raspberry Pi installer
```

---

## ✅ **Benefits**

1. **Same codebase** for both environments
2. **Test on Windows** before deploying to Pi
3. **No manual configuration** needed
4. **Git pull works** on both platforms
5. **Maintainability** - one code to rule them all!

---

## 🧪 **Testing Workflow**

```
Windows PC                    Raspberry Pi 5
─────────────                ──────────────────
1. Edit code                 4. Git pull
2. Test in mock mode         5. Service restarts
3. Git commit & push         6. Real hardware works
```

---

## 🚀 **Commands**

### Windows:
```bash
# Quick test
test_windows.bat

# OR manual
python app\app.py
```

### Raspberry Pi:
```bash
# Update code
cd ~/smart-classroom
git pull origin main
sudo systemctl restart smart-classroom

# View logs
sudo journalctl -u smart-classroom -f
```

**Perfect for development and production!** 🎉
