"""Console entry point that validates resources before running the desktop app."""

from __future__ import annotations

import runpy
from pathlib import Path

from startup_check import validate_resources


def main() -> None:
    validate_resources()
    # main.py is installed as a Python module alongside this launcher.
    runpy.run_path(str(Path(__file__).resolve().with_name("main.py")), run_name="__main__")


if __name__ == "__main__":
    main()
