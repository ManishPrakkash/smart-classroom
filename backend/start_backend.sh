#!/bin/bash

# ── Smart Switch – Backend Startup Script ─────────────────────────────────────
# Run:  bash start_backend.sh
# Works on Raspberry Pi (real GPIO) and any Linux/macOS dev machine (mock GPIO).
# ─────────────────────────────────────────────────────────────────────────────

set -e

# Colours
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Smart Switch – Backend Startup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ── 1. Load .env if present ───────────────────────────────────────────────────
if [ -f ".env" ]; then
    echo -e "${GREEN}[1/4] Loading .env ...${NC}"
    # Export every KEY=VALUE line (strips surrounding quotes, skips comments)
    set -o allexport
    # shellcheck disable=SC1091
    source .env
    set +o allexport
    echo "      Done."
else
    echo -e "${YELLOW}[1/4] No .env file found – using system environment.${NC}"
fi
echo ""

# ── 2. Python virtual environment ────────────────────────────────────────────
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${GREEN}[2/4] Creating virtual environment ...${NC}"
    python3 -m venv "$VENV_DIR"
else
    echo -e "${GREEN}[2/4] Virtual environment already exists.${NC}"
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "      Active: $(which python)"
echo ""

# ── 3. Install / update dependencies ─────────────────────────────────────────
echo -e "${GREEN}[3/4] Installing dependencies from requirements.txt ...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "      Done."
echo ""

# ── 4. Start Flask app ────────────────────────────────────────────────────────
echo -e "${GREEN}[4/4] Starting Flask backend ...${NC}"

# Default to mock GPIO on non-Pi machines
if [ -f "/proc/cpuinfo" ] && grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "      Running on Raspberry Pi – using real GPIO."
    export USE_MOCK_GPIO="${USE_MOCK_GPIO:-0}"
else
    echo -e "      ${YELLOW}Not a Raspberry Pi – enabling mock GPIO.${NC}"
    export USE_MOCK_GPIO="${USE_MOCK_GPIO:-1}"
fi

echo ""
python app.py
