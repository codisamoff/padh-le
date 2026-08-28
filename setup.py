"""Setuptools configuration for the Padh Le desktop application."""

from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent


def read_requirements() -> list[str]:
    return [
        line.strip()
        for line in (ROOT / "requirements-app.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def resource_data_files() -> list[tuple[str, list[str]]]:
    files = [("padhle", ["config.yaml", "yolo11n.pt"])]
    for path in sorted((ROOT / "assets").rglob("*")):
        if path.is_file():
            files.append((str(Path("padhle") / path.parent.relative_to(ROOT)), [str(path.relative_to(ROOT))]))
    return files


setup(
    name="padh-le",
    version="1.0.0",
    description="Padh Le desktop study monitor using webcam face and eye detection",
    python_requires=">=3.11,<3.12",
    install_requires=read_requirements(),
    packages=find_packages(include=("audio", "audio.*", "detection", "detection.*", "monitoring", "monitoring.*", "ui", "ui.*", "utils", "utils.*")),
    py_modules=["main", "padhle_launcher", "resource_paths", "startup_check"],
    data_files=resource_data_files(),
    include_package_data=True,
    entry_points={"console_scripts": ["padhle=padhle_launcher:main"]},
)
