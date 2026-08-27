import time
import yaml
import cv2
import pygame
import math
import subprocess
import threading
import tempfile
import os
import queue


# ============================================================
# CONFIGURATION
# ============================================================

EYES_CLOSED_DELAY = 2.0
NO_FACE_DELAY = 2.0
PHONE_DELAY = 1.0

EYE_CLOSED_THRESHOLD = 0.20

UTH_JAA_SOUND = "assets/sounds/uth_jaa.mp3"
DEKH_DEKH_SOUND = "assets/sounds/arvind_dekh.mp3"
PHONE_SOUND = "assets/sounds/padhle.mp3"

YOLO_WORKER = ".venv/bin/python"
PHONE_WORKER = "detection/phone_worker.py"


# ============================================================
# LOAD CONFIG
# ============================================================

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cam_cfg = config["camera"]
face_cfg = config["face_detection"]


# ============================================================
# AUDIO MANAGER
# ============================================================

class AudioManager:

    def __init__(self):
        pygame.mixer.init()

        self.sounds = {
            "eyes_closed": pygame.mixer.Sound(UTH_JAA_SOUND),
            "face_missing": pygame.mixer.Sound(DEKH_DEKH_SOUND),
            "phone": pygame.mixer.Sound(PHONE_SOUND),
        }

        self.lock = threading.Lock()
        self.playing = False

    def play(self, name):

        with self.lock:

            if self.playing:
                return False

            self.playing = True

        thread = threading.Thread(
            target=self._play_worker,
            args=(name,),
            daemon=True
        )

        thread.start()

        return True

    def _play_worker(self, name):

        try:

            sound = self.sounds[name]

            print(f"🔊 Playing: {name}")

            sound.play()

            while pygame.mixer.get_busy():
                time.sleep(0.05)

        finally:

            with self.lock:
                self.playing = False

    def is_playing(self):

        with self.lock:
            return self.playing

    def close(self):

        pygame.mixer.quit()


# ============================================================
# PHONE DETECTOR
# ============================================================

class PhoneWorker:

    def __init__(self):

        self.process = subprocess.Popen(
            [
                YOLO_WORKER,
                PHONE_WORKER
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        # Wait for worker startup
        while True:

            line = self.process.stdout.readline().strip()

            if line == "PHONE_WORKER_READY":

                print("📱 Phone detector ready.")

                break

            if not line:
                break

    def detect(self, frame):

        # Save current frame temporarily
        fd, path = tempfile.mkstemp(
            suffix=".jpg",
            dir="/tmp"
        )

        os.close(fd)

        try:

            cv2.imwrite(path, frame)

            self.process.stdin.write(path + "\n")
            self.process.stdin.flush()

            result = self.process.stdout.readline().strip()

            return result == "PHONE"

        finally:

            try:
                os.remove(path)
            except OSError:
                pass

    def close(self):

        try:

            self.process.stdin.write("QUIT\n")
            self.process.stdin.flush()

        except Exception:
            pass

        try:
            self.process.terminate()
        except Exception:
            pass


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(cam_cfg["index"])

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    cam_cfg["width"]
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    cam_cfg["height"]
)

cap.set(
    cv2.CAP_PROP_FPS,
    cam_cfg["fps"]
)

if not cap.isOpened():

    raise RuntimeError(
        f"Could not open camera index {cam_cfg['index']}"
    )


# ============================================================
# FACE DETECTOR
# ============================================================

from detection.face_detector import FaceDetector

detector = FaceDetector(
    model_path=face_cfg["model_path"],
    num_faces=face_cfg["num_faces"],
    min_detection_confidence=
        face_cfg["min_face_detection_confidence"],
    min_tracking_confidence=
        face_cfg["min_tracking_confidence"],
)


# ============================================================
# START SYSTEMS
# ============================================================

audio = AudioManager()
phone_detector = PhoneWorker()


# ============================================================
# EYE LANDMARKS
# ============================================================

LEFT_EYE = [
    33,
    160,
    158,
    133,
    153,
    144
]

RIGHT_EYE = [
    362,
    385,
    387,
    263,
    373,
    380
]


# ============================================================
# MATH
# ============================================================

def distance(p1, p2):

    return math.sqrt(
        (p1[0] - p2[0]) ** 2 +
        (p1[1] - p2[1]) ** 2
    )


def eye_aspect_ratio(
    landmarks,
    eye_indices,
    width,
    height
):

    points = []

    for index in eye_indices:

        lm = landmarks[index]

        points.append(
            (
                lm.x * width,
                lm.y * height
            )
        )

    vertical_1 = distance(
        points[1],
        points[5]
    )

    vertical_2 = distance(
        points[2],
        points[4]
    )

    horizontal = distance(
        points[0],
        points[3]
    )

    if horizontal == 0:
        return 0.0

    return (
        vertical_1 +
        vertical_2
    ) / (2.0 * horizontal)


# ============================================================
# STATE
# ============================================================

no_face_since = None
eyes_closed_since = None
phone_since = None

no_face_alert_played = False
eyes_closed_alert_played = False
phone_alert_played = False

prev_time = time.time()


# ============================================================
# START
# ============================================================

print()
print("==========================================")
print("              PADH LE")
print("==========================================")
print()
print("👤 Face missing  -> ARVIND DEKH")
print("👁️ Eyes closed   -> UTH JAA")
print("📱 Phone detected -> PADHLE")
print()
print("Sounds will NEVER overlap.")
print()
print("Press Q to quit.")
print()


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        ret, frame = cap.read()

        if not ret:

            print("Failed to read camera frame.")
            break

        h, w = frame.shape[:2]

        # ----------------------------------------------------
        # FACE
        # ----------------------------------------------------

        result = detector.detect(frame)

        face_found = bool(
            result.face_landmarks
        )


        # ====================================================
        # FACE FOUND
        # ====================================================

        if face_found:

            landmarks = result.face_landmarks[0]

            no_face_since = None
            no_face_alert_played = False


            # ------------------------------------------------
            # EYES
            # ------------------------------------------------

            left_ear = eye_aspect_ratio(
                landmarks,
                LEFT_EYE,
                w,
                h
            )

            right_ear = eye_aspect_ratio(
                landmarks,
                RIGHT_EYE,
                w,
                h
            )

            average_ear = (
                left_ear +
                right_ear
            ) / 2.0

            eyes_closed = (
                average_ear <
                EYE_CLOSED_THRESHOLD
            )


            # =================================================
            # EYES CLOSED
            # =================================================

            if eyes_closed:

                if eyes_closed_since is None:

                    eyes_closed_since = time.time()

                closed_duration = (
                    time.time() -
                    eyes_closed_since
                )

                if (
                    closed_duration >=
                    EYES_CLOSED_DELAY
                    and
                    not eyes_closed_alert_played
                ):

                    if audio.play("eyes_closed"):

                        print(
                            "👁️ Eyes closed -> "
                            "UTH JAA"
                        )

                        eyes_closed_alert_played = True

                eye_status = "EYES CLOSED"
                eye_color = (0, 0, 255)


            # =================================================
            # EYES OPEN
            # =================================================

            else:

                eyes_closed_since = None
                eyes_closed_alert_played = False

                eye_status = "EYES OPEN"
                eye_color = (0, 255, 0)


            # =================================================
            # PHONE DETECTION
            # =================================================

            phone_found = phone_detector.detect(frame)


            if phone_found:

                if phone_since is None:

                    phone_since = time.time()

                phone_duration = (
                    time.time() -
                    phone_since
                )

                if (
                    phone_duration >= PHONE_DELAY
                    and
                    not phone_alert_played
                ):

                    if audio.play("phone"):

                        print(
                            "📱 PHONE DETECTED -> "
                            "PADHLE"
                        )

                        phone_alert_played = True

                phone_status = "PHONE DETECTED"
                phone_color = (0, 0, 255)

            else:

                phone_since = None
                phone_alert_played = False

                phone_status = "NO PHONE"
                phone_color = (0, 255, 0)


            # =================================================
            # FACE BOX
            # =================================================

            if config["ui"]["show_landmarks"]:

                xs = [
                    lm.x * w
                    for lm in landmarks
                ]

                ys = [
                    lm.y * h
                    for lm in landmarks
                ]

                x_min = int(min(xs))
                x_max = int(max(xs))

                y_min = int(min(ys))
                y_max = int(max(ys))

                cv2.rectangle(
                    frame,
                    (x_min, y_min),
                    (x_max, y_max),
                    (0, 255, 0),
                    2
                )


                for index in LEFT_EYE + RIGHT_EYE:

                    lm = landmarks[index]

                    x = int(lm.x * w)
                    y = int(lm.y * h)

                    cv2.circle(
                        frame,
                        (x, y),
                        3,
                        (255, 255, 0),
                        -1
                    )


            # =================================================
            # UI
            # =================================================

            cv2.putText(
                frame,
                "STUDENT DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                eye_status,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                eye_color,
                2
            )

            cv2.putText(
                frame,
                phone_status,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                phone_color,
                2
            )

            cv2.putText(
                frame,
                f"EAR: {average_ear:.3f}",
                (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )


        # ====================================================
        # FACE NOT FOUND
        # ====================================================

        else:

            eyes_closed_since = None
            eyes_closed_alert_played = False

            phone_since = None
            phone_alert_played = False


            if no_face_since is None:

                no_face_since = time.time()

            no_face_duration = (
                time.time() -
                no_face_since
            )


            if (
                no_face_duration >=
                NO_FACE_DELAY
                and
                not no_face_alert_played
            ):

                if audio.play("face_missing"):

                    print(
                        "👤 Student missing -> "
                        "ARVIND DEKH"
                    )

                    no_face_alert_played = True


            cv2.putText(
                frame,
                "STUDENT NOT DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                f"Missing: {no_face_duration:.1f}s",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )


        # ====================================================
        # FPS
        # ====================================================

        now = time.time()

        fps = (
            1.0 /
            (now - prev_time)
            if now > prev_time
            else 0.0
        )

        prev_time = now


        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )


        # ====================================================
        # SHOW
        # ====================================================

        cv2.imshow(
            "Padh Le",
            frame
        )


        if cv2.waitKey(1) & 0xFF == ord("q"):

            break


finally:

    print()
    print("Stopping Padh Le...")

    phone_detector.close()
    audio.close()

    detector.close()

    cap.release()

    cv2.destroyAllWindows()

    print("Stopped.")
