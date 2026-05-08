#!/bin/bash
# =============================================================================
# Hybrid Rocket Simulator - Setup and Run Script (Linux/Mac)
# =============================================================================
# This script will:
#   1. Check Python installation
#   2. Install required dependencies
#   3. Launch the GUI
# =============================================================================

echo ""
echo "============================================"
echo "  Hybrid Rocket Simulator - Setup"
echo "============================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    echo "Please install Python 3.8 or higher."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-tk"
    echo "  Mac: brew install python3"
    exit 1
fi

echo "[OK] Python found:"
python3 --version
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip3 is not available!"
    echo "Please install pip: sudo apt install python3-pip"
    exit 1
fi

echo "[OK] pip found"
echo ""

# Check for tkinter (common issue on Linux)
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARNING] tkinter is not installed!"
    echo "Install it with:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "  Fedora: sudo dnf install python3-tkinter"
    echo "  Mac: brew install python-tk"
    echo ""
fi

# Install dependencies
echo "Installing dependencies..."
echo ""
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[WARNING] Some packages may have failed to install."
    echo "Check the error messages above."
    echo ""
fi

echo ""
echo "============================================"
echo "  Starting Hybrid Rocket Simulator..."
echo "============================================"
echo ""

# Run the application
python3 main.py
