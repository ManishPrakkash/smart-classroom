# Connection Troubleshooting Guide

## Common Connection Issues

### Issue: "Failed to connect to server"

This means the mobile app cannot reach the Raspberry Pi. Follow these steps:

## 1. Check Backend is Running

On your Raspberry Pi:
```bash
cd ~/smart-classroom/backend
source venv/bin/activate
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

## 2. Verify WiFi Connection

**Both devices MUST be on the same WiFi network:**

### On Raspberry Pi:
```bash
# Check IP address
hostname -I
# Should show: 10.27.253.96 (or similar)

# Check WiFi connection
iwconfig wlan0
```

### On Mobile Device:
- Settings → WiFi
- Confirm connected to **same network** as Pi
- Note the network name

## 3. Test Backend Directly

### From Raspberry Pi itself:
```bash
curl http://localhost:5000/status
# Should return: {"status": "Relay Server Running"}

curl http://localhost:5000/devices
# Should return: ["light1", "light2", ...]
```

### From Another Computer on Same Network:
Open browser and visit:
```
http://10.27.253.96:5000/status
```

If this works → Backend is fine, issue is with mobile app config  
If this fails → Backend or network issue

## 4. Check Firewall (On Raspberry Pi)

```bash
# Check if firewall is blocking port 5000
sudo ufw status

# If active, allow port 5000
sudo ufw allow 5000

# Or disable firewall temporarily for testing
sudo ufw disable
```

## 5. Verify Mobile App Configuration

### Check config.js:
```javascript
// frontend/src/config.js
if (isNative()) {
  return 'http://10.27.253.96:5000';  // ← Must match Pi IP!
}
```

### After changing config.js:
```bash
# Rebuild the app
cd frontend
npm run build
npx cap sync

# Then rebuild in Android Studio/Xcode
```

## 6. Check Browser Console (Web Version)

If testing in browser first:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for error messages

Common errors:
- **"Failed to fetch"** → Network connectivity issue
- **"CORS error"** → Backend CORS not configured (should be fixed)
- **"ERR_CONNECTION_REFUSED"** → Backend not running
- **"ERR_NAME_NOT_RESOLVED"** → Wrong IP address

## 7. Network Debugging Commands

### On Raspberry Pi:
```bash
# Check if server is listening
sudo netstat -tulpn | grep :5000
# Should show: tcp 0.0.0.0:5000  LISTEN  python

# Check active connections
sudo ss -tuln | grep 5000
```

### From Mobile/Computer:
```bash
# Ping the Raspberry Pi
ping 10.27.253.96

# Check if port 5000 is accessible (Linux/Mac)
nc -zv 10.27.253.96 5000

# Or use telnet (Windows)
telnet 10.27.253.96 5000
```

## 8. Router Issues

Some routers have **AP Isolation** enabled, which prevents devices from talking to each other:

1. Access your router settings (usually 192.168.1.1 or 192.168.0.1)
2. Look for "AP Isolation" or "Client Isolation"
3. **Disable** it
4. Save and reboot router

## Quick Diagnostic Script

Run this on your Raspberry Pi to check everything:

```bash
#!/bin/bash

echo "=== Smart Classroom Diagnostics ==="
echo ""

echo "1. IP Address:"
hostname -I

echo ""
echo "2. Flask Process:"
ps aux | grep "python app.py" | grep -v grep

echo ""
echo "3. Port 5000 Status:"
sudo netstat -tulpn | grep :5000

echo ""
echo "4. Testing Local Connection:"
curl -s http://localhost:5000/status || echo "❌ Backend not responding locally"

echo ""
echo "5. Testing Network Connection:"
curl -s http://$(hostname -I | awk '{print $1}'):5000/status || echo "❌ Backend not accessible from network"

echo ""
echo "6. WiFi Status:"
iwconfig wlan0 2>/dev/null | grep ESSID

echo ""
echo "=== End Diagnostics ==="
```

## Still Not Working?

### Try these:

1. **Restart Backend:**
   ```bash
   # Kill existing process
   sudo kill -9 $(sudo lsof -t -i:5000)
   
   # Start fresh
   python app.py
   ```

2. **Use Static IP on Pi:**
   ```bash
   # Edit dhcpcd.conf
   sudo nano /etc/dhcpcd.conf
   
   # Add at end:
   interface wlan0
   static ip_address=10.27.253.96/24
   static routers=10.27.253.1
   static domain_name_servers=8.8.8.8
   
   # Restart networking
   sudo systemctl restart dhcpcd
   ```

3. **Check App Logs:**
   
   **Web Browser:**
   - F12 → Console tab → Look for errors
   
   **Android (via ADB):**
   ```bash
   adb logcat | grep -i "chromium\|console"
   ```
   
   **iOS (via Xcode):**
   - Window → Devices and Simulators → View Device Logs

4. **Test with Simple Request:**
   
   In browser DevTools console:
   ```javascript
   fetch('http://10.27.253.96:5000/devices')
     .then(r => r.json())
     .then(console.log)
     .catch(console.error)
   ```

## Expected Console Output (When Working)

When the app connects successfully, you should see:
```
🔍 Attempting to fetch devices from: http://10.27.253.96:5000/devices
🌐 API Base URL: http://10.27.253.96:5000
📱 Running in Capacitor: true
✅ Response received: 200 OK
📋 Devices received: ["light1", "light2", "light3", "light4", "fan1", "fan2", "fan3", "fan4"]
✅ Successfully loaded 8 devices
```

## Common Solutions Summary

| Problem | Solution |
|---------|----------|
| Backend not running | `python app.py` on Pi |
| Wrong IP address | Update `config.js` and rebuild |
| Different WiFi networks | Connect both to same network |
| Firewall blocking | `sudo ufw allow 5000` |
| AP Isolation enabled | Disable in router settings |
| Forgot to rebuild app | `npm run build && npx cap sync` |
| CORS errors | Verify `flask-cors` installed |

Need more help? Check the browser console logs for detailed error messages!
