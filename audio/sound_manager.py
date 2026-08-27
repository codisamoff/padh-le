import os
import time
import threading
import queue
import pygame


class SoundManager:
    """
    Sequential warning audio system.

    Only ONE sound plays at a time.
    New warnings are placed into a queue and play
    after the current sound has completely finished.
    """

    def __init__(self, sounds_dir="assets/sounds"):
        self.sounds_dir = sounds_dir

        self.sound_queue = queue.Queue()
        self.running = True

        # Prevent the same detection from filling the queue
        # repeatedly while it remains active.
        self.last_queued = {}
        self.cooldowns = {
            "eyes_closed": 5.0,
            "face_missing": 5.0,
            "phone_detected": 5.0,
        }

        pygame.mixer.init()

        self.worker = threading.Thread(
            target=self._worker,
            daemon=True
        )
        self.worker.start()

    def _worker(self):
        while self.running:
            try:
                event_name, filename = self.sound_queue.get(
                    timeout=0.1
                )
            except queue.Empty:
                continue

            try:
                path = os.path.join(self.sounds_dir, filename)

                if not os.path.exists(path):
                    print(f"[SOUND ERROR] File not found: {path}")
                    continue

                print(f"[SOUND] Playing: {filename}")

                sound = pygame.mixer.Sound(path)
                sound.play()

                # CRITICAL:
                # Do not start another sound until this one
                # has completely finished.
                while pygame.mixer.get_busy() and self.running:
                    time.sleep(0.05)

                print(f"[SOUND] Finished: {filename}")

            except Exception as e:
                print(f"[SOUND ERROR] {e}")

            finally:
                self.sound_queue.task_done()

    def play_warning(self, event_name, filename):
        """
        Queue a warning.

        Returns True if queued.
        Returns False if blocked by cooldown.
        """

        now = time.monotonic()
        last = self.last_queued.get(event_name, 0)

        cooldown = self.cooldowns.get(event_name, 5.0)

        if now - last < cooldown:
            return False

        self.last_queued[event_name] = now

        self.sound_queue.put((event_name, filename))

        print(f"[SOUND] Queued: {filename}")

        return True

    def is_playing(self):
        """
        True when audio is currently playing OR waiting
        in the queue.
        """
        return pygame.mixer.get_busy() or not self.sound_queue.empty()

    def wait_until_finished(self):
        """
        Wait until all queued sounds have finished.
        """
        self.sound_queue.join()

    def close(self):
        self.running = False

        try:
            pygame.mixer.stop()
            pygame.mixer.quit()
        except Exception:
            pass
