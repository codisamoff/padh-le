FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYGAME_HIDE_SUPPORT_PROMPT=1

WORKDIR /opt/padhle

# Runtime libraries for OpenCV's GUI backend and Pygame/ALSA audio. Camera,
# display, and audio devices remain host-provided and are attached at run time.
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libasound2 \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 padhle \
    && useradd --uid 10001 --gid padhle --create-home --shell /usr/sbin/nologin padhle

# Keep the heavyweight, pinned dependency layer cacheable while application
# source changes.
COPY requirements-app.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-app.txt

COPY setup.py pyproject.toml MANIFEST.in README.md ./
COPY main.py padhle_launcher.py resource_paths.py startup_check.py config.yaml yolo11n.pt ./
COPY assets ./assets
COPY audio ./audio
COPY detection ./detection
COPY monitoring ./monitoring
COPY ui ./ui
COPY utils ./utils

RUN python -m pip install --no-deps . \
    && python -m startup_check

USER padhle
CMD ["padhle"]
