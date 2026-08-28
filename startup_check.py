"""Validate Padh Le's bundled runtime files before opening hardware devices."""

from __future__ import annotations

import argparse
import importlib
import multiprocessing
import platform
import shutil
import sys
from pathlib import Path

from resource_paths import resource_path, resource_root


REQUIRED_RESOURCES = (
    "config.yaml",
    "yolo11n.pt",
    "assets/models/face_landmarker.task",
    "assets/sounds",
)
EXPECTED_SOUNDS = ("arvind_dekh.mp3", "dekh_dekh.mp3", "padhle.mp3", "phone_warning.mp3", "uth_jaa.mp3")
RUNTIME_IMPORTS = ("cv2", "mediapipe", "numpy", "pygame", "yaml", "ultralytics")


def missing_resources() -> list[Path]:
    missing = [resource_path(item) for item in REQUIRED_RESOURCES if not resource_path(item).exists()]
    sounds_dir = resource_path("assets/sounds")
    if sounds_dir.is_dir():
        missing.extend(sounds_dir / name for name in EXPECTED_SOUNDS if not (sounds_dir / name).is_file())
    return missing


def validate_resources() -> None:
    """Raise a clear error if the installed/source bundle is incomplete."""
    missing = missing_resources()
    if missing:
        formatted = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(
            "Padh Le cannot start because required resources are missing:\n"
            f"{formatted}\n"
            "Reinstall the application or set PADHLE_RESOURCE_DIR to a complete resource directory."
        )


def _print_system_diagnostics() -> None:
    print(f"Python: {sys.version.split()[0]} ({platform.machine()})")
    print(f"Platform: {platform.platform()}")
    disk = shutil.disk_usage(resource_root())
    print(f"Disk free at resource root: {disk.free / (1024 ** 3):.2f} GiB")
    try:
        memory = Path("/proc/meminfo").read_text(encoding="ascii")
        for key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            line = next((item for item in memory.splitlines() if item.startswith(key + ":")), None)
            if line:
                print(line)
    except (OSError, UnicodeError):
        print("Memory/swap: unavailable on this platform")


def _check_imports() -> bool:
    passed = True
    for name in RUNTIME_IMPORTS:
        try:
            module = importlib.import_module(name)
            print(f"Import OK: {name} ({getattr(module, '__version__', 'version unknown')})")
        except Exception as error:
            passed = False
            print(f"Import FAILED: {name}: {error}")
    return passed


def _check_camera() -> bool:
    import cv2
    camera = cv2.VideoCapture(0)
    available = bool(camera.isOpened())
    camera.release()
    print(f"Camera index 0: {'available' if available else 'unavailable'}")
    return available


def _check_audio() -> bool:
    import pygame
    try:
        pygame.mixer.init()
        pygame.mixer.quit()
        print("Audio mixer: available")
        return True
    except Exception as error:
        print(f"Audio mixer: unavailable ({error})")
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        return False


def _face_probe_worker() -> None:
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    detector = vision.FaceLandmarker.create_from_options(
        vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(resource_path("assets/models/face_landmarker.task"))),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
    )
    detector.close()


def _probe_face_landmarker() -> bool:
    """Probe in a child so a native SIGKILL cannot take down this diagnostic parent."""
    child = multiprocessing.get_context("spawn").Process(target=_face_probe_worker)
    child.start()
    child.join()
    if child.exitcode == 0:
        print("FaceLandmarker construction: passed")
        return True
    if child.exitcode is not None and child.exitcode < 0:
        print(f"FaceLandmarker construction: native process signal {-child.exitcode} (SIGKILL cannot be caught by Python)")
    else:
        print(f"FaceLandmarker construction: failed (child exit code {child.exitcode})")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Padh Le without constructing FaceLandmarker by default.")
    parser.add_argument("--probe-face-landmarker", action="store_true", help="probe native construction in an isolated child")
    parser.add_argument("--check-camera", action="store_true", help="probe webcam index 0")
    parser.add_argument("--check-audio", action="store_true", help="probe the Pygame audio mixer")
    parser.add_argument("--skip-imports", action="store_true", help="skip runtime import checks")
    args = parser.parse_args()
    _print_system_diagnostics()
    try:
        validate_resources()
    except FileNotFoundError as error:
        print(error)
        return 1
    print(f"Padh Le resource check passed: {resource_root()}")
    passed = args.skip_imports or _check_imports()
    if args.check_camera:
        try:
            passed = _check_camera() and passed
        except Exception as error:
            print(f"Camera check failed: {error}")
            passed = False
    if args.check_audio:
        try:
            passed = _check_audio() and passed
        except Exception as error:
            print(f"Audio check failed: {error}")
            passed = False
    if args.probe_face_landmarker:
        passed = _probe_face_landmarker() and passed
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
