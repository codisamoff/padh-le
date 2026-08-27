class EyeDetector:
    """
    Detects whether the eyes are open or closed using
    MediaPipe FaceLandmarker eye landmarks.
    """

    LEFT = {
        "left": 33,
        "right": 133,
        "top": 159,
        "bottom": 145,
    }

    RIGHT = {
        "left": 362,
        "right": 263,
        "top": 386,
        "bottom": 374,
    }

    @staticmethod
    def eye_ratio(landmarks, eye):
        left = landmarks[eye["left"]]
        right = landmarks[eye["right"]]
        top = landmarks[eye["top"]]
        bottom = landmarks[eye["bottom"]]

        width = abs(right.x - left.x)
        height = abs(bottom.y - top.y)

        if width < 0.0001:
            return 0.0

        return height / width

    def analyze(self, landmarks):
        left_ratio = self.eye_ratio(landmarks, self.LEFT)
        right_ratio = self.eye_ratio(landmarks, self.RIGHT)

        average_ratio = (left_ratio + right_ratio) / 2.0

        # Initial threshold.
        # We will calibrate this if necessary.
        eyes_open = average_ratio >= 0.18

        return {
            "eyes_open": eyes_open,
            "left_ratio": left_ratio,
            "right_ratio": right_ratio,
            "ratio": average_ratio,
        }
