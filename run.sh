#!/bin/bash
# FirstVerify Dynamic Reporting Engine - Startup Script for Linux/Mac

echo ""
echo "========================================"
echo "FirstVerify Reporting Engine v1.0"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from https://www.python.org"
    exit 1
fi

echo "[1/4] Python found - checking version..."
python3 --version

# Check if venv exists
if [ ! -d "venv" ]; then
    echo ""
    echo "[2/4] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate venv
echo "[3/4] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Install/upgrade dependencies
echo "[4/4] Installing dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "========================================"
echo "Starting FirstVerify Reporting Engine..."
echo "========================================"
echo ""
echo "Dashboard: http://127.0.0.1:8000"
echo "API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
