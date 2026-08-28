"""Single source of truth for Padh Le runtime resource locations."""

from __future__ import annotations

import os
import sys
import sysconfig
from pathlib import Path


def _candidate_roots() -> list[Path]:
    """Return possible resource roots in priority order without using the CWD."""
    candidates: list[Path] = []

    configured_root = os.environ.get("PADHLE_RESOURCE_DIR")
    if configured_root:
        candidates.append(Path(configured_root).expanduser().resolve())

    if getattr(sys, "frozen", False):
        # PyInstaller sets _MEIPASS for both one-file and one-directory builds.
        candidates.append(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)))

    module_root = Path(__file__).resolve().parent
    candidates.extend((module_root, module_root / "padhle"))
    # ``data_files`` is installed under Python's data scheme (normally the
    # active virtual environment or interpreter prefix), not the working dir.
    candidates.append(Path(sysconfig.get_path("data")) / "padhle")

    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def resource_root() -> Path:
    """Locate the directory containing Padh Le's bundled resources."""
    for candidate in _candidate_roots():
        if (candidate / "config.yaml").is_file():
            return candidate
    return _candidate_roots()[0]


def resource_path(relative_path: str | Path) -> Path:
    """Resolve a bundled resource for source, installed, Docker, and PyInstaller runs."""
    relative = Path(relative_path)
    if relative.is_absolute():
        raise ValueError("resource_path() requires a path relative to the application root")

    for candidate in _candidate_roots():
        path = candidate / relative
        if path.exists():
            return path
    return resource_root() / relative
