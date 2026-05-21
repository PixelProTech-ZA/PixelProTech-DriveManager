#!/bin/bash

# ============================================================
#   PIXELPROTECH SOLUTIONS — DRIVE MANAGER INSTALLER
#   IT Support . Computer Repairs . Gauteng
#   076 645 9348 . pixelprotechsolutions@gmail.com
# ============================================================

RESET="\033[0m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
BOLD="\033[1m"

echo ""
echo -e "${CYAN}============================================================${RESET}"
echo -e "${BOLD}  PIXELPROTECH SOLUTIONS — DRIVE MANAGER INSTALLER${RESET}"
echo -e "  IT Support . Computer Repairs . Gauteng"
echo -e "  076 645 9348 . pixelprotechsolutions@gmail.com"
echo -e "${CYAN}============================================================${RESET}"
echo ""

# ── Check Python ─────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    PY="python3"
elif command -v python &>/dev/null; then
    PY="python"
else
    echo -e "${RED}[!] Python not found.${RESET}"
    echo ""
    echo -e "    Install it with one of these commands:"
    echo ""
    echo -e "    ${YELLOW}Ubuntu/Debian:${RESET}  sudo apt install python3 python3-pip python3-tk"
    echo -e "    ${YELLOW}Fedora:${RESET}         sudo dnf install python3 python3-pip python3-tkinter"
    echo -e "    ${YELLOW}macOS:${RESET}          brew install python3"
    echo -e "    ${YELLOW}Or visit:${RESET}       https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK]${RESET} Python found: $($PY --version)"
echo ""

# ── Check tkinter ─────────────────────────────────────────────
$PY -c "import tkinter" &>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[!] tkinter not found. Attempting to install...${RESET}"
    if command -v apt &>/dev/null; then
        sudo apt install python3-tk -y
    elif command -v dnf &>/dev/null; then
        sudo dnf install python3-tkinter -y
    elif command -v brew &>/dev/null; then
        brew install python-tk
    else
        echo -e "${RED}[!] Could not auto-install tkinter.${RESET}"
        echo "    Please install python3-tk manually for your OS."
        exit 1
    fi
fi
echo -e "${GREEN}[OK]${RESET} tkinter available."
echo ""

# ── Install psutil ────────────────────────────────────────────
echo -e "[..] Installing required dependency: psutil..."
$PY -m pip install psutil --quiet --break-system-packages 2>/dev/null || \
$PY -m pip install psutil --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Failed to install psutil. Check your internet connection.${RESET}"
    exit 1
fi
echo -e "${GREEN}[OK]${RESET} psutil installed."
echo ""

# ── Check .py file ────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_FILE="$SCRIPT_DIR/PixelProTech_DriveManager.py"

if [ ! -f "$PY_FILE" ]; then
    echo -e "${RED}[!] PixelProTech_DriveManager.py not found in this folder.${RESET}"
    echo "    Make sure install.sh and PixelProTech_DriveManager.py"
    echo "    are in the same folder, then try again."
    echo ""
    exit 1
fi
echo -e "${GREEN}[OK]${RESET} PixelProTech_DriveManager.py found."
echo ""

# ── Make executable ───────────────────────────────────────────
chmod +x "$PY_FILE"

# ── Launch ────────────────────────────────────────────────────
echo -e "${CYAN}============================================================${RESET}"
echo -e "${BOLD}  ALL DONE. Launching Drive Manager now...${RESET}"
echo -e "${CYAN}============================================================${RESET}"
echo ""
sleep 1

$PY "$PY_FILE"
