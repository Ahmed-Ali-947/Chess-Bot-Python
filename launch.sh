#!/bin/bash
echo "================================================"
echo "   Chess AI - Linux/macOS Launcher"
echo "================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Install from https://python.org"
    exit 1
fi

# Check Tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] tkinter not found. Install it with:"
    echo "  Ubuntu/Debian:  sudo apt-get install python3-tk"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo "  Arch:           sudo pacman -S tk"
    exit 1
fi

# Install pip dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt --quiet

# Launch
echo "Launching Chess AI..."
python3 run.py
