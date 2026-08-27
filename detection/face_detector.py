"""
Wraps MediaPipe's FaceLandmarker (Tasks API) for real-time face + landmark detection.
Phase 2 scope: detect a face and expose its landmarks. Eye/head-pose interpretation
happens in later modules (eye_detector.py, head_pose.py) — this module just detects.
"""
import time
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions


class FaceDetector:
    def __init__(self, model_path: str, num_faces: int = 1,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        base_options = BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=num_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._detector = vision.FaceLandmarker.create_from_options(options)
        self._start_time = time.time()

    def detect(self, bgr_frame):
        """
        Takes an OpenCV BGR frame. Returns the raw FaceLandmarkerResult
        (result.face_landmarks is a list of faces, each a list of landmarks
        with .x/.y/.z in normalized [0,1] coords). Empty list if no face found.
        """
        import cv2
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.time() - self._start_time) * 1000)
        return self._detector.detect_for_video(mp_image, timestamp_ms)

    def close(self):
        self._detector.close()
