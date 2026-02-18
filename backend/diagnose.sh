#!/bin/bash

# Smart Classroom Connection Diagnostics
# Run this on your Raspberry Pi to check all connection requirements

echo "========================================"
echo "  Smart Classroom Connection Check"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get IP address
IP=$(hostname -I | awk '{print $1}')

echo "1. IP ADDRESS"
echo "   Current IP: $IP"
if [ "$IP" == "10.27.253.96" ]; then
    echo -e "   ${GREEN}✓ Matches expected IP (10.27.253.96)${NC}"
else
    echo -e "   ${YELLOW}⚠ IP is different! Update config.js to: $IP${NC}"
fi
echo ""

echo "2. WIFI CONNECTION"
WIFI=$(iwconfig wlan0 2>/dev/null | grep ESSID | awk -F'"' '{print $2}')
if [ -n "$WIFI" ]; then
    echo -e "   ${GREEN}✓ Connected to WiFi: $WIFI${NC}"
else
    echo -e "   ${RED}✗ Not connected to WiFi${NC}"
fi
echo ""

echo "3. PYTHON INSTALLATION"
if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version)
    echo -e "   ${GREEN}✓ $PYTHON_VER installed${NC}"
else
    echo -e "   ${RED}✗ Python3 not found${NC}"
fi
echo ""

echo "4. FLASK SERVER PROCESS"
if pgrep -f "python.*app.py" > /dev/null; then
    PID=$(pgrep -f "python.*app.py")
    echo -e "   ${GREEN}✓ Flask server running (PID: $PID)${NC}"
else
    echo -e "   ${RED}✗ Flask server NOT running${NC}"
    echo "   Start with: python app.py"
fi
echo ""

echo "5. PORT 5000 STATUS"
if sudo lsof -i :5000 &> /dev/null; then
    echo -e "   ${GREEN}✓ Port 5000 is in use${NC}"
    sudo lsof -i :5000 | grep LISTEN
else
    echo -e "   ${RED}✗ Port 5000 is not listening${NC}"
fi
echo ""

echo "6. LOCALHOST TEST"
STATUS=$(curl -s http://localhost:5000/status 2>&1)
if echo "$STATUS" | grep -q "Relay Server Running"; then
    echo -e "   ${GREEN}✓ Backend responding on localhost${NC}"
    echo "   Response: $STATUS"
else
    echo -e "   ${RED}✗ Backend not responding on localhost${NC}"
    echo "   Error: $STATUS"
fi
echo ""

echo "7. NETWORK TEST"
STATUS=$(curl -s http://$IP:5000/status 2>&1)
if echo "$STATUS" | grep -q "Relay Server Running"; then
    echo -e "   ${GREEN}✓ Backend accessible from network${NC}"
else
    echo -e "   ${RED}✗ Backend not accessible from network${NC}"
    echo "   This means other devices cannot connect!"
fi
echo ""

echo "8. DEVICES ENDPOINT TEST"
DEVICES=$(curl -s http://localhost:5000/devices 2>&1)
if echo "$DEVICES" | grep -q "light"; then
    echo -e "   ${GREEN}✓ Devices endpoint working${NC}"
    echo "   Devices: $DEVICES"
else
    echo -e "   ${RED}✗ Devices endpoint not working${NC}"
fi
echo ""

echo "9. FIREWALL STATUS"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | grep Status | awk '{print $2}')
    if [ "$UFW_STATUS" == "active" ]; then
        echo -e "   ${YELLOW}⚠ Firewall is active${NC}"
        if sudo ufw status | grep -q "5000"; then
            echo -e "   ${GREEN}✓ Port 5000 is allowed${NC}"
        else
            echo -e "   ${RED}✗ Port 5000 is blocked!${NC}"
            echo "   Fix with: sudo ufw allow 5000"
        fi
    else
        echo -e "   ${GREEN}✓ Firewall is inactive${NC}"
    fi
else
    echo "   Firewall (ufw) not installed"
fi
echo ""

echo "========================================"
echo "  SUMMARY & RECOMMENDATIONS"
echo "========================================"
echo ""

# Check if everything is good
ERRORS=0

if [ "$IP" != "10.27.253.96" ]; then
    echo -e "${YELLOW}⚠ Update config.js with new IP: $IP${NC}"
    echo "   Location: frontend/src/config.js"
    echo "   Line 13: return 'http://$IP:5000';"
    echo "   Then rebuild: npm run build && npx cap sync"
    echo ""
    ERRORS=1
fi

if ! pgrep -f "python.*app.py" > /dev/null; then
    echo -e "${RED}✗ START THE BACKEND SERVER!${NC}"
    echo "   cd ~/smart-classroom/backend"
    echo "   source venv/bin/activate"
    echo "   python app.py"
    echo ""
    ERRORS=1
fi

if ! curl -s http://$IP:5000/status | grep -q "Relay Server Running"; then
    echo -e "${RED}✗ Backend not accessible from network${NC}"
    echo "   Check firewall settings"
    echo "   Verify Flask is binding to 0.0.0.0 (not localhost)"
    echo ""
    ERRORS=1
fi

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ ALL CHECKS PASSED! ✓✓✓${NC}"
    echo ""
    echo "Your Raspberry Pi is ready!"
    echo "Mobile app should connect to: http://$IP:5000"
    echo ""
    echo "Test from mobile browser first:"
    echo "  http://$IP:5000/status"
else
    echo "Please fix the issues above and run this script again."
    echo ""
    echo "For detailed help, see: TROUBLESHOOTING.md"
fi

echo ""
echo "========================================"
