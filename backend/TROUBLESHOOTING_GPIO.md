# GPIO Troubleshooting Guide

## Problem: Raspberry Pi Not Responding to Frontend Commands

If the frontend shows state changes but the physical relays don't switch:

### Quick Diagnosis

Run the diagnostic test:
```bash
cd backend
source venv/bin/activate
python test_gpio.py
```

Watch the output for errors and warnings.

---

## Common Issues & Solutions

### 1. Mock GPIO Enabled on Raspberry Pi

**Symptom:** Frontend works, backend logs show commands, but relays don't switch

**Check:**
```bash
echo $USE_MOCK_GPIO
```

**Fix:**
```bash
# In your terminal session:
export USE_MOCK_GPIO=0

# Or edit start_backend.sh and remove the line:
# export USE_MOCK_GPIO=1

# Then restart:
./start_backend.sh
```

---

### 2. GPIO Permissions Error

**Symptom:** Error messages like "Permission denied" or "GPIO access denied"

**Fix:**
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout and login (or reboot)
sudo reboot

# Verify group membership
groups | grep gpio
```

---

### 3. Wrong Pin Factory (Raspberry Pi 5)

**Symptom:** Error about "pin factory" or "lgpio not found" on RPi 5

**Check:**
```bash
python3 << EOF
from gpiozero import Device
Device.ensure_pin_factory()
print(type(Device.pin_factory).__name__)
EOF
```

**Fix for RPi 5:**
```bash
pip install lgpio
# The start_backend.sh should do this automatically
```

---

### 4. pigpiod Not Running (Raspberry Pi 3/4)

**Symptom:** "PiGPIOFactory: connection refused" or similar

**Check:**
```bash
sudo systemctl status pigpiod
```

**Fix:**
```bash
# Start pigpiod
sudo systemctl start pigpiod

# Enable on boot
sudo systemctl enable pigpiod

# Verify it's running
sudo systemctl status pigpiod
```

---

### 5. Wrong Relay Logic (Active High vs Active Low)

**Symptom:** Relays work but are inverted (ON when should be OFF)

Most relay modules are **active-low** (the default in our code):
- `relay.on()` → GPIO pin goes LOW → Relay activates
- `relay.off()` → GPIO pin goes HIGH → Relay deactivates

If your relays are **active-high**, edit `backend/app.py`:

```python
# Line ~192, change this:
def create_relays():
    return {
        name: OutputDevice(pin, active_high=False)  # ← Change to True
        for name, pin in devices.items()
    }
```

**Test which type you have:**
```python
python3 << EOF
from gpiozero import OutputDevice
import time

relay = OutputDevice(17, active_high=False)
relay.on()
print("Relay should be ON now")
time.sleep(3)
relay.off()
print("Relay should be OFF now")
EOF
```

If the relay behaves opposite to what's printed, change `active_high=True`.

---

### 6. Incorrect Wiring

**Check your connections:**

**Output Pins (Relay Control):**
| Device | GPIO | Physical Pin |
|--------|------|--------------|
| light1 | 17   | Pin 11       |
| light2 | 18   | Pin 12       |
| light3 | 27   | Pin 13       |
| light4 | 22   | Pin 15       |
| fan1   | 23   | Pin 16       |
| fan2   | 24   | Pin 18       |
| fan3   | 25   | Pin 22       |
| fan4   | 5    | Pin 29       |

**Relay Module Wiring:**
```
Raspberry Pi          Relay Module
────────────         ──────────────
GPIO 17       ──────> IN1
GPIO 18       ──────> IN2
...
5V (Pin 2)    ──────> VCC
GND (Pin 6)   ──────> GND
```

**Verify with a multimeter:**
- Measure voltage on GPIO pin
- ON state should be ~0V (for active_low)
- OFF state should be ~3.3V

---

### 7. Relay Module Not Powered

**Check:**
- Relay module VCC connected to 5V (Pin 2 or Pin 4)
- Relay module GND connected to GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
- Relay LED should light up when powered

**Test power:**
```bash
# Check if 5V is available
vcgencmd get_throttled
# Output should be: throttled=0x0
```

---

### 8. Backend Not Running or Crashed

**Check backend status:**
```bash
# See if app.py is running
ps aux | grep app.py

# Check backend logs
cd backend
tail -f logs/backend.log  # if logging to file
```

**Restart backend:**
```bash
cd backend
./start_backend.sh
```

---

## Verification Checklist

After fixing, verify with:

1. **Test GPIO directly:**
   ```bash
   python test_gpio.py
   ```

2. **Check backend logs:**
   ```bash
   # Watch logs in real-time
   cd backend
   python app.py
   
   # In another terminal, test control:
   curl http://localhost:8000/control/light1/on
   curl http://localhost:8000/control/light1/off
   ```

3. **Test from frontend:**
   - Open browser DevTools → Network tab
   - Click a device toggle
   - Check if request goes to backend
   - Check backend terminal for log messages

4. **Physical verification:**
   - Listen for relay "click" sound
   - Watch for relay LED indicator
   - Measure GPIO voltage with multimeter

---

## Still Not Working?

Check the main [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) or create an issue with:
- Output of `test_gpio.py`
- Backend logs when toggling a device
- Raspberry Pi model and OS version: `cat /etc/os-release`
- Photo of your wiring setup
