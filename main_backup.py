import time
import yaml
import cv2
import pygame
import math

from detection.face_detector import FaceDetector


# ============================================================
# CONFIGURATION
# ============================================================

EYES_CLOSED_DELAY = 2.0
NO_FACE_DELAY = 2.0

EYE_CLOSED_THRESHOLD = 0.20

UTH_JAA_SOUND = "assets/sounds/uth_jaa.mp3"
DEKH_DEKH_SOUND = "assets/sounds/arvind_dekh.mp3"


# ============================================================
# LOAD CONFIG
# ============================================================

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cam_cfg = config["camera"]
face_cfg = config["face_detection"]


# ============================================================
# AUDIO
# ============================================================

pygame.mixer.init()

try:
    uth_jaa = pygame.mixer.Sound(UTH_JAA_SOUND)
    dekh_dekh = pygame.mixer.Sound(DEKH_DEKH_SOUND)

    print("Audio loaded successfully.")

except Exception as e:
    raise RuntimeError(f"Could not load audio: {e}")


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

detector = FaceDetector(
    model_path=face_cfg["model_path"],
    num_faces=face_cfg["num_faces"],
    min_detection_confidence=
        face_cfg["min_face_detection_confidence"],
    min_tracking_confidence=
        face_cfg["min_tracking_confidence"],
)


# ============================================================
# EYE LANDMARKS
# ============================================================

# MediaPipe Face Mesh / Face Landmarker landmarks.
#
# Left eye:
# 33, 160, 158, 133, 153, 144
#
# Right eye:
# 362, 385, 387, 263, 373, 380

LEFT_EYE = [33, 160, 158, 133, 153, 144]

RIGHT_EYE = [362, 385, 387, 263, 373, 380]


# ============================================================
# EAR CALCULATION
# ============================================================

def distance(p1, p2):
    return math.sqrt(
        (p1[0] - p2[0]) ** 2 +
        (p1[1] - p2[1]) ** 2
    )


def eye_aspect_ratio(landmarks, eye_indices, width, height):

    points = []

    for index in eye_indices:

        lm = landmarks[index]

        points.append(
            (
                lm.x * width,
                lm.y * height
            )
        )

    # Vertical eye distances
    vertical_1 = distance(points[1], points[5])
    vertical_2 = distance(points[2], points[4])

    # Horizontal eye distance
    horizontal = distance(points[0], points[3])

    if horizontal == 0:
        return 0.0

    ear = (
        vertical_1 +
        vertical_2
    ) / (2.0 * horizontal)

    return ear


# ============================================================
# STATE VARIABLES
# ============================================================

no_face_since = None
eyes_closed_since = None

no_face_alert_played = False
eyes_closed_alert_played = False

prev_time = time.time()


print()
print("==========================================")
print(" SMART STUDY MONITOR")
print("==========================================")
print()
print("Face missing  -> dekh-dekh sound")
print("Eyes closed   -> uth-jaa sound")
print()
print(f"Face delay: {NO_FACE_DELAY} seconds")
print(f"Eyes delay: {EYES_CLOSED_DELAY} seconds")
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

            print("Failed to read frame.")
            break


        h, w = frame.shape[:2]


        # ----------------------------------------------------
        # DETECT FACE
        # ----------------------------------------------------

        result = detector.detect(frame)

        face_found = bool(result.face_landmarks)


        # ====================================================
        # FACE FOUND
        # ====================================================

        if face_found:

            landmarks = result.face_landmarks[0]


            # ------------------------------------------------
            # RESET FACE-MISSING STATE
            # ------------------------------------------------

            no_face_since = None
            no_face_alert_played = False


            # ------------------------------------------------
            # CALCULATE EYE EAR
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


            # ------------------------------------------------
            # DETERMINE EYE STATE
            # ------------------------------------------------

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


                # ---------------------------------------------
                # PLAY UTH JAA
                # ---------------------------------------------

                if (
                    closed_duration >=
                    EYES_CLOSED_DELAY
                    and
                    not eyes_closed_alert_played
                ):

                    print(
                        "Eyes closed -> "
                        "playing UTH JAA"
                    )

                    uth_jaa.play()

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


            # ------------------------------------------------
            # DRAW FACE BOX
            # ------------------------------------------------

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


                # Draw eye landmarks

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


            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

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
                0.75,
                eye_color,
                2
            )


            cv2.putText(
                frame,
                f"EAR: {average_ear:.3f}",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )


        # ====================================================
        # FACE NOT FOUND
        # ====================================================

        else:

            # -----------------------------------------------
            # RESET EYE STATE
            # -----------------------------------------------

            eyes_closed_since = None
            eyes_closed_alert_played = False


            # -----------------------------------------------
            # START FACE-MISSING TIMER
            # -----------------------------------------------

            if no_face_since is None:

                no_face_since = time.time()


            no_face_duration = (
                time.time() -
                no_face_since
            )


            # -----------------------------------------------
            # PLAY DEKH-DEKH
            # -----------------------------------------------

            if (
                no_face_duration >=
                NO_FACE_DELAY
                and
                not no_face_alert_played
            ):

                print(
                    "Student not detected -> "
                    "playing DEKH DEKH"
                )

                dekh_dekh.play()

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
            1.0 / (now - prev_time)
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
        # SHOW CAMERA
        # ====================================================

        cv2.imshow(
            "Padh Le",
            frame
        )


        # ====================================================
        # QUIT
        # ====================================================

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


finally:

    detector.close()

    cap.release()

    cv2.destroyAllWindows()

    pygame.mixer.quit()
