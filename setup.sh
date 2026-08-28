#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_dir="$project_dir/.venv"

echo "======================================"
echo "        Padh Le Setup"
echo "======================================"
echo

# --------------------------------------------------
# Find Python 3.11
# --------------------------------------------------

if command -v python3.11 >/dev/null 2>&1; then
    python_cmd="$(command -v python3.11)"
elif command -v python3 >/dev/null 2>&1; then
    python_cmd="$(command -v python3)"
else
    echo "ERROR: Python 3.11 is required."
    exit 1
fi

"$python_cmd" - <<'PY'
import sys

if sys.version_info[:2] != (3, 11):
    raise SystemExit(
        f"ERROR: Python 3.11 is required; found {sys.version.split()[0]}"
    )

print(f"Python {sys.version.split()[0]} detected.")
PY

# --------------------------------------------------
# Disk check
# --------------------------------------------------

available_kb="$(df -Pk "$project_dir" | awk 'NR == 2 {print $4}')"

if [[ "${available_kb:-0}" -lt 4194304 ]]; then
    echo
    echo "WARNING:"
    echo "Less than 4 GB of free disk space is available."
    echo "Padh Le dependencies may require significant storage."
    echo
fi

# --------------------------------------------------
# Create virtual environment
# --------------------------------------------------

if [[ -e "$venv_dir" && ! -d "$venv_dir" ]]; then
    echo "ERROR: $venv_dir exists but is not a directory."
    exit 1
fi

if [[ ! -d "$venv_dir" ]]; then
    echo "Creating Python virtual environment..."
    "$python_cmd" -m venv "$venv_dir"
fi

venv_python="$venv_dir/bin/python"

"$venv_python" - <<'PY'
import sys

if sys.version_info[:2] != (3, 11):
    raise SystemExit(
        f"ERROR: .venv must use Python 3.11; found {sys.version}"
    )
PY

# --------------------------------------------------
# Upgrade pip
# --------------------------------------------------

echo
echo "Upgrading pip..."
"$venv_python" -m pip install --upgrade pip

# --------------------------------------------------
# Install normal application dependencies
# --------------------------------------------------

echo
echo "Installing Padh Le dependencies..."

"$venv_python" -m pip install \
    --no-cache-dir \
    mediapipe==0.10.21 \
    numpy==1.26.4 \
    opencv-contrib-python==4.10.0.84 \
    PyYAML==6.0.2 \
    pygame==2.6.1 \
    protobuf==4.25.3

# --------------------------------------------------
# Install CPU-only PyTorch
# --------------------------------------------------

echo
echo "Installing CPU-only PyTorch..."
echo "This avoids the large NVIDIA/CUDA packages."

"$venv_python" -m pip install \
    --no-cache-dir \
    torch==2.4.1 \
    torchvision==0.19.1 \
    --index-url https://download.pytorch.org/whl/cpu

# --------------------------------------------------
# Install Ultralytics without replacing PyTorch
# --------------------------------------------------

echo
echo "Installing Ultralytics..."

"$venv_python" -m pip install \
    --no-cache-dir \
    ultralytics==8.3.0

# --------------------------------------------------
# Verify runtime
# --------------------------------------------------

echo
echo "Checking Padh Le imports..."

"$venv_python" - <<'PY'
import cv2
import mediapipe
import numpy
import pygame
import torch
import torchvision
import ultralytics
import yaml

print("All required imports passed.")
print("OpenCV:", cv2.__version__)
print("MediaPipe:", mediapipe.__version__)
print("NumPy:", numpy.__version__)
print("PyTorch:", torch.__version__)
print("Torch CUDA available:", torch.cuda.is_available())
print("Torchvision:", torchvision.__version__)
print("Ultralytics:", ultralytics.__version__)
PY

# --------------------------------------------------
# Validate application resources
# --------------------------------------------------

echo
echo "Running Padh Le startup check..."

"$venv_python" -m startup_check

echo
echo "======================================"
echo " Padh Le setup completed successfully"
echo "======================================"
echo
echo "Start Padh Le with:"
echo
echo "    ./run.sh"
echo
