import sys
import cv2
from ultralytics import YOLO

MODEL = "yolo11n.pt"

model = YOLO(MODEL)

print("PHONE_WORKER_READY", flush=True)

while True:
    line = sys.stdin.readline()

    if not line:
        break

    line = line.strip()

    if line == "QUIT":
        break

    # Main program sends a temporary image filename.
    image_path = line

    frame = cv2.imread(image_path)

    if frame is None:
        print("ERROR", flush=True)
        continue

    results = model.predict(
        source=frame,
        conf=0.25,
        imgsz=640,
        device="cpu",
        verbose=False,
    )

    phone_found = False

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            class_id = int(box.cls[0])

            if class_id == 67:
                phone_found = True
                break

        if phone_found:
            break

    print("PHONE" if phone_found else "NO_PHONE", flush=True)

