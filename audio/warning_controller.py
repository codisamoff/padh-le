import os
import time
import threading
import pygame


class WarningController:
    """
    Central warning audio controller.

    Priority:
        1. phone_detected
        2. eyes_closed
        3. face_missing

    Behaviour:
        - Only one warning plays at a time.
        - Higher-priority warnings immediately interrupt lower-priority warnings.
        - Active warnings continuously replay.
        - When a warning condition becomes false, it will not replay.
        - If another condition is active, the appropriate warning takes over.
    """

    PRIORITY = {
        "phone_detected": 3,
        "eyes_closed": 2,
        "face_missing": 1,
    }

    def __init__(self, sounds_dir):
        self.sounds_dir = str(sounds_dir)

        self.sounds = {}

        self.active_event = None
        self.active_sound = None
        self.active_filename = None

        self.conditions = {
            "eyes_closed": False,
            "face_missing": False,
            "phone_detected": False,
        }

        self.filenames = {}

        self.running = True
        self.lock = threading.RLock()

        pygame.mixer.init()

        self.worker = threading.Thread(
            target=self._worker,
            daemon=True,
        )

        self.worker.start()

    # ============================================================
    # LOAD SOUND
    # ============================================================

    def _get_sound(self, filename):
        if filename not in self.sounds:
            path = os.path.join(
                self.sounds_dir,
                filename,
            )

            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"Sound file not found: {path}"
                )

            self.sounds[filename] = pygame.mixer.Sound(path)

        return self.sounds[filename]

    # ============================================================
    # FIND HIGHEST PRIORITY ACTIVE WARNING
    # ============================================================

    def _get_highest_priority_event(self):
        active = [
            event
            for event, is_active in self.conditions.items()
            if is_active
        ]

        if not active:
            return None

        return max(
            active,
            key=lambda event: self.PRIORITY.get(event, 0),
        )

    # ============================================================
    # SET CONDITION
    # ============================================================

    def set_condition(self, event_name, active, filename):
        with self.lock:

            if event_name not in self.conditions:
                self.conditions[event_name] = False

            self.conditions[event_name] = active
            self.filenames[event_name] = filename

            print(
                f"[WARNING] {event_name} "
                f"{'ACTIVE' if active else 'CLEARED'}"
            )

            desired_event = self._get_highest_priority_event()

            # ----------------------------------------------------
            # No warning should be active
            # ----------------------------------------------------

            if desired_event is None:

                if self.active_event is not None:
                    print(
                        f"[WARNING] {self.active_event} "
                        f"cleared -> stopping audio"
                    )

                    try:
                        pygame.mixer.stop()
                    except Exception:
                        pass

                    self.active_event = None
                    self.active_sound = None
                    self.active_filename = None

                return

            desired_filename = self.filenames.get(
                desired_event
            )

            if desired_filename is None:
                return

            # ----------------------------------------------------
            # Different warning has priority
            # ----------------------------------------------------

            if self.active_event != desired_event:

                self._play_new_warning(
                    desired_event,
                    desired_filename,
                )

    # ============================================================
    # PLAY NEW WARNING
    # ============================================================

    def _play_new_warning(self, event_name, filename):

        try:
            # Stop whatever is currently playing.
            pygame.mixer.stop()

        except Exception:
            pass

        try:
            sound = self._get_sound(filename)

            print(
                f"[WARNING] {event_name} "
                f"-> playing {filename}"
            )

            sound.play()

            self.active_event = event_name
            self.active_sound = sound
            self.active_filename = filename

        except Exception as e:

            print(
                f"[WARNING AUDIO ERROR] {e}"
            )

    # ============================================================
    # WORKER
    # ============================================================

    def _worker(self):

        while self.running:

            time.sleep(0.05)

            with self.lock:

                if self.active_event is None:
                    continue

                # Sound is still playing.
                if pygame.mixer.get_busy():
                    continue

                # ------------------------------------------------
                # Sound finished.
                # ------------------------------------------------

                desired_event = self._get_highest_priority_event()

                # ------------------------------------------------
                # No conditions active.
                # ------------------------------------------------

                if desired_event is None:

                    print(
                        f"[WARNING] {self.active_event} "
                        f"finished and no warning remains"
                    )

                    self.active_event = None
                    self.active_sound = None
                    self.active_filename = None

                    continue

                desired_filename = self.filenames.get(
                    desired_event
                )

                if desired_filename is None:
                    continue

                # ------------------------------------------------
                # Another warning became higher priority.
                # ------------------------------------------------

                if desired_event != self.active_event:

                    self._play_new_warning(
                        desired_event,
                        desired_filename,
                    )

                    continue

                # ------------------------------------------------
                # Same warning still active.
                # Replay it.
                # ------------------------------------------------

                if self.conditions.get(
                    self.active_event,
                    False,
                ):

                    try:

                        print(
                            f"[WARNING] "
                            f"{self.active_event} still active "
                            f"-> replaying"
                        )

                        self.active_sound.play()

                    except Exception as e:

                        print(
                            f"[WARNING AUDIO ERROR] {e}"
                        )

                else:

                    print(
                        f"[WARNING] "
                        f"{self.active_event} cleared"
                    )

                    self.active_event = None
                    self.active_sound = None
                    self.active_filename = None

    # ============================================================
    # STOP ALL
    # ============================================================

    def stop_all(self):

        with self.lock:

            try:
                pygame.mixer.stop()
            except Exception:
                pass

            self.active_event = None
            self.active_sound = None
            self.active_filename = None

            for event in self.conditions:
                self.conditions[event] = False

    # ============================================================
    # CLOSE
    # ============================================================

    def close(self):

        self.running = False

        try:
            pygame.mixer.stop()
            pygame.mixer.quit()
        except Exception:
            pass
