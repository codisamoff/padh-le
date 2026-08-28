# Padh Le

Padh Le is an offline Python desktop study monitor. It uses a webcam and MediaPipe FaceLandmarker to detect a student, estimate eye closure, show an OpenCV camera window, and play local audio alerts. Existing YOLO phone-detection modules and the bundled `yolo11n.pt` model are retained for the project.

## Requirements

- Python 3.11 (the project is intentionally constrained to Python 3.11).
- A webcam available to OpenCV.
- A desktop GUI session for the camera window.
- An audio output device for Pygame alerts.
- Linux, Windows, or macOS can run the source application when their Python wheels and hardware permissions are supported. The automated Windows executable is the preferred Windows desktop distribution.

Padh Le is a local desktop application. Its models and alert sounds are bundled; normal operation does not download models at runtime. The installed dependency set includes Ultralytics and its PyTorch dependency because the existing phone-detection modules use them.

## Linux installation

From the repository root:

```bash
chmod +x setup.sh run.sh
./setup.sh
```

The script checks for Python 3.11, creates `.venv` only when it does not already exist, warns when less than 5 GB is free, installs the pinned application, verifies imports, and validates the bundled resources.

Start Padh Le with:

```bash
./run.sh
```

You can also use standard packaging commands:

```bash
python3.11 -m pip install .
padhle
```

For development from the checkout, use `python3.11 -m pip install -e .`. `requirements-app.txt` is the reproducible runtime dependency list; `requirements-dev.txt` additionally pins PyInstaller for builds.

To validate without constructing the native FaceLandmarker (the default):

```bash
python -m startup_check
```

Optional hardware checks are explicit:

```bash
python -m startup_check --check-camera --check-audio
```

To investigate FaceLandmarker initialization, use the isolated probe:

```bash
python -m startup_check --probe-face-landmarker
```

The probe runs construction in a child process. A native SIGKILL/SIGABRT cannot be caught by Python in the application process; the parent instead reports the signal and exits cleanly. The current Linux environment's cause is not conclusively identified: imports and model-file validation succeed, but native FaceLandmarker construction must be tested with the selected dependency set and host memory/CPU libraries.

## Windows

For typical Windows users, use the GitHub Actions-generated `PadhLe-Windows.zip`, extract it, and run `PadhLe.exe`. It is built with Python 3.11 and includes `config.yaml`, `assets/`, `yolo11n.pt`, and MediaPipe resources.

To run from source in PowerShell instead:

```powershell
.\setup.ps1
.\run.ps1
```

If PowerShell blocks local scripts, use an execution policy appropriate to your organization rather than changing system-wide Python packages.

## Docker (Linux desktop hosts)

Build the reproducible Linux image:

```bash
docker build -t padhle:latest .
```

Check the image resources without opening devices or a GUI:

```bash
docker run --rm --entrypoint python padhle:latest -m startup_check
```

To start with an X11 desktop, webcam, and PulseAudio, first allow the local container to use your X server and export the host-specific device group IDs:

```bash
xhost +si:localuser:$(id -un)
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
export VIDEO_GID="$(stat -c '%g' /dev/video0)"
export AUDIO_GID="$(stat -c '%g' /dev/snd)"
docker compose up
```

The Compose file maps `/dev/video0`, `/dev/snd`, the X11 socket, and the host PulseAudio socket. It expects a Linux graphical session with PulseAudio-compatible audio and these devices present. For a direct Docker invocation, the equivalent essentials are:

```bash
docker run --rm \
  --device /dev/video0 --device /dev/snd \
  --group-add "$(stat -c '%g' /dev/video0)" \
  --group-add "$(stat -c '%g' /dev/snd)" \
  -e DISPLAY -e XAUTHORITY=/tmp/.Xauthority \
  -e PULSE_SERVER=unix:/tmp/pulse/native \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "$XAUTHORITY:/tmp/.Xauthority:ro" \
  -v "$XDG_RUNTIME_DIR/pulse/native:/tmp/pulse/native" \
  padhle:latest
```

This is a Linux-only host-integration example, not a guarantee for every desktop configuration. Hardware permissions and audio systems vary; ALSA-only hosts may need a tailored audio-device configuration.

## Limitations

Docker makes the Python environment reproducible, but it does not automatically virtualize webcams, speakers, microphones, or desktop GUIs across operating systems. Linux containers can receive host devices and an X11/PulseAudio connection when explicitly configured. Ordinary Linux Docker does not provide native Windows GUI/webcam behavior; use the Windows `.exe` for normal Windows desktop use. macOS Docker Desktop does not generally offer practical direct Linux-container webcam/GUI/audio passthrough for this application.

Padh Le is not an Android or iOS application. Docker does not turn this desktop architecture into a mobile app; mobile support requires a separate mobile UI, camera integration, and platform-specific build architecture.
