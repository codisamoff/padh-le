import cv2
from ultralytics import YOLO


class PhoneDetector:
    """
    Detects mobile phones using YOLO.

    YOLO runs in the separate .venv environment.
    """

    PHONE_CLASS_ID = 67

    def __init__(self, model_path="yolo11n.pt", confidence=0.25):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):
        """
        Returns True when a cell phone is detected.
        """

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            imgsz=640,
            verbose=False,
            device="cpu",
        )

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                class_id = int(box.cls[0])

                if class_id == self.PHONE_CLASS_ID:
                    confidence = float(box.conf[0])

                    if confidence >= self.confidence:
                        return True

        return False
