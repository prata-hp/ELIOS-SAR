from pathlib import Path
import datetime
import json
import os
import socket
import sys
import time
import cv2
from ultralytics import YOLO
GCS_HOST = os.getenv('GCS_HOST', '127.0.0.1')
VIDEO_PORT = int(os.getenv('VIDEO_PORT', 8765))
AI_PORT = int(os.getenv('AI_PORT', 8766))
CAMERA_DEVICE = int(os.getenv('CAMERA_DEVICE', 0))
CONFIDENCE_THRESHOLD = float(os.getenv('YOLO_CONFIDENCE', '0.20'))
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR / 'ELIOS-SAR-RPI'
MODEL_PATH = PROJECT_DIR / 'models' / 'rgb' / 'rgb_disaster.pt'
if not MODEL_PATH.exists():
    MODEL_PATH = Path('models/rgb/rgb_disaster.pt')
print(f'[MODEL] Loading YOLO from: {MODEL_PATH} (Confidence: {CONFIDENCE_THRESHOLD})')
model = YOLO(str(MODEL_PATH))
print(f'[MODEL] Available classes: {model.names}')
print(f'[NET] Connecting to Video -> {GCS_HOST}:{VIDEO_PORT}')
video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_socket.connect((GCS_HOST, VIDEO_PORT))
print('[NET] Video socket connected')
print(f'[NET] Connecting to AI -> {GCS_HOST}:{AI_PORT}')
ai_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ai_socket.connect((GCS_HOST, AI_PORT))
print('[NET] AI socket connected')
cap = cv2.VideoCapture(CAMERA_DEVICE)
frame_id = 0
print('\n' + '=' * 60)
print(' LIVE AI STREAMING & ANNOTATION ACTIVE')
print(" Press 'q' on the preview window to exit")
print('=' * 60 + '\n')

def draw_annotations(frame, detections, fps, inf_time):
    for det in detections:
        bbox = det['bbox']
        x1, y1, x2, y2 = map(int, bbox)
        label = det['label'].upper()
        conf = det['confidence']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        tag = f'{label} {conf:.2f}'
        (w, h), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + w + 8, max(22, y1)), (0, 255, 0), -1)
        cv2.putText(frame, tag, (x1 + 4, max(16, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    hud = [f'MODEL: {MODEL_PATH.name}', f'INFERENCE: {inf_time:.1f} ms ({fps:.1f} FPS)', f'DETECTIONS: {len(detections)}']
    for i, line in enumerate(hud):
        cv2.putText(frame, line, (10, 25 + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)
    return frame
while True:
    ok, frame = cap.read()
    if not ok:
        time.sleep(0.05)
        continue
    frame_id += 1
    t0 = time.perf_counter()
    results = model.predict(source=frame, conf=CONFIDENCE_THRESHOLD, device='cpu', verbose=False)
    t1 = time.perf_counter()
    inf_time_ms = (t1 - t0) * 1000.0
    fps = 1000.0 / inf_time_ms if inf_time_ms > 0 else 0.0
    detections = []
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls_id = int(box.cls[0])
            raw_label = str(model.names[cls_id]).lower()
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({'label': raw_label, 'confidence': round(conf, 2), 'bbox': [round(float(x1), 1), round(float(y1), 1), round(float(x2), 1), round(float(y2), 1)]})
    annotated_frame = draw_annotations(frame.copy(), detections, fps, inf_time_ms)
    success, encoded = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    if success:
        video_socket.sendall(encoded.tobytes())
    ai_message = {'type': 'PERSON_DETECTION', 'source': 'DRONE-01', 'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'frame_id': frame_id, 'inference_time_ms': round(inf_time_ms, 1), 'inference_fps': round(fps, 1), 'detections': detections}
    payload = (json.dumps(ai_message) + '\n').encode('utf-8')
    ai_socket.sendall(payload)
    cv2.imshow('ELIOS-SAR Live AI', annotated_frame)
    if cv2.waitKey(1) & 255 == ord('q'):
        break
cap.release()
video_socket.close()
ai_socket.close()
cv2.destroyAllWindows()
