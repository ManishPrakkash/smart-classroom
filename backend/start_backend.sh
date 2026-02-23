#!/bin/bash

# ──────────────────────────────────────────────────────────────────────────────
# Smart Classroom Backend Startup Script
# Supports: Raspberry Pi 3/4 (pigpio), Raspberry Pi 5 (lgpio), Dev machines
# ──────────────────────────────────────────────────────────────────────────────

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Always run from the directory containing this script ──────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║      Smart Classroom – Backend Server        ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: Load .env ─────────────────────────────────────────────────────────
echo -e "${GREEN}[1/5] Environment ...${NC}"
if [ -f ".env" ]; then
    set -o allexport
    # shellcheck disable=SC1091
    source .env
    set +o allexport
    echo "      Loaded .env"
else
    echo -e "      ${YELLOW}No .env found – using defaults.${NC}"
fi

# Timezone & log level defaults
export TZ="${TZ:-Asia/Kolkata}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export TF_CPP_MIN_LOG_LEVEL="${TF_CPP_MIN_LOG_LEVEL:-2}"
export TF_ENABLE_ONEDNN_OPTS="${TF_ENABLE_ONEDNN_OPTS:-0}"
echo "      TZ=$TZ  LOG_LEVEL=$LOG_LEVEL"

# ── Step 2: GPIO & Camera detection ──────────────────────────────────────────
echo -e "${GREEN}[2/5] GPIO & Camera ...${NC}"
if [ -f "/proc/cpuinfo" ] && grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    export USE_MOCK_GPIO="${USE_MOCK_GPIO:-0}"
    
    # Detect Raspberry Pi model
    if grep -q "Raspberry Pi 5" /proc/cpuinfo 2>/dev/null; then
        RPI_MODEL="5"
        echo "      Raspberry Pi 5 detected"
        echo "      GPIO backend: lgpio (required for RPi 5)"
        # gpiozero will automatically use lgpio on RPi 5 if installed
    else
        RPI_MODEL="3/4"
        echo "      Raspberry Pi 3/4 detected"
        echo "      GPIO backend: pigpio"
        # Ensure pigpiod is running
        if ! systemctl is-active --quiet pigpiod; then
            echo -e "      ${YELLOW}Starting pigpiod daemon...${NC}"
            sudo systemctl start pigpiod 2>/dev/null || echo -e "      ${YELLOW}Warning: Could not start pigpiod${NC}"
        fi
    fi
    
    # Check for camera
    if [ -e "/dev/video0" ] || libcamera-hello --list-cameras 2>&1 | grep -q "Available cameras"; then
        echo "      Camera detected: PiCamera2 enabled"
        export CAMERA_AVAILABLE=1
    else
        echo -e "      ${YELLOW}No camera detected${NC}"
        export CAMERA_AVAILABLE=0
    fi
else
    export USE_MOCK_GPIO="${USE_MOCK_GPIO:-1}"
    echo -e "      ${YELLOW}Dev machine – mock GPIO enabled (USE_MOCK_GPIO=1)${NC}"
    echo -e "      ${YELLOW}Camera: USB webcam (if available)${NC}"
    export CAMERA_AVAILABLE=0
fi

# ── Step 3: Python virtual environment ───────────────────────────────────────
echo -e "${GREEN}[3/5] Virtual environment ...${NC}"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "      Creating venv ..."
    python3 -m venv "$VENV_DIR"
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "      Python: $(which python)  ($(python --version))"

# ── Step 4: Dependencies ──────────────────────────────────────────────────────
echo -e "${GREEN}[4/5] Dependencies ...${NC}"
pip install --quiet --upgrade pip

# Install base requirements
pip install --quiet -r requirements.txt

# Install GPIO backend based on Pi model
if [ "$USE_MOCK_GPIO" = "0" ]; then
    if [ "$RPI_MODEL" = "5" ]; then
        echo "      Installing lgpio for Raspberry Pi 5..."
        pip install --quiet lgpio || echo -e "      ${YELLOW}Warning: lgpio install failed${NC}"
    else
        # pigpio already in requirements.txt for RPi 3/4
        echo "      Using pigpio for Raspberry Pi 3/4"
    fi
fi

# Install camera support if camera detected
if [ "$CAMERA_AVAILABLE" = "1" ]; then
    echo "      Installing camera dependencies..."
    # picamera2 is usually pre-installed on Pi OS Bullseye+
    pip install --quiet picamera2 2>/dev/null || echo "      picamera2 already installed (system package)"
fi

echo "      All packages installed."

# ── Step 5: Start Flask ───────────────────────────────────────────────────────
echo -e "${GREEN}[5/5] Starting Flask on port 8000 ...${NC}"
echo ""
echo -e "${CYAN}  Backend URL : http://0.0.0.0:8000${NC}"
echo -e "${CYAN}  Timezone    : $TZ${NC}"
echo -e "${CYAN}  Mock GPIO   : $USE_MOCK_GPIO${NC}"
if [ -n "$RPI_MODEL" ]; then
    echo -e "${CYAN}  Pi Model    : $RPI_MODEL${NC}"
fi
if [ "$CAMERA_AVAILABLE" = "1" ]; then
    echo -e "${CYAN}  Camera      : Available${NC}"
fi
echo ""

exec python app.py
