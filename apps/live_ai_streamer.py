from __future__ import annotations
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import cv2
from drone.config import DRONE_ID
from src.perception.camera import Camera
from src.perception.rgb_detector import RGBDetector
from src.communication.ai_websocket import AIWebSocketClient
from src.communication.video_websocket import VideoWebSocketClient
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('ELIOS-SAR-AI')
MODEL_PATH = os.getenv('MODEL_PATH', 'models/rgb/rgb_disaster.pt')
CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', '640'))
CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', '480'))
CAMERA_FPS = int(os.getenv('CAMERA_FPS', '20'))
CAMERA_DEVICE = int(os.getenv('CAMERA_DEVICE', '0'))
YOLO_CONFIDENCE = float(os.getenv('YOLO_CONFIDENCE', '0.35'))

def draw_detections(frame, detections, inference_time_ms):
    for detection in detections:
        bbox = detection.get('bbox')
        confidence = detection.get('confidence', 0.0)
        label = detection.get('label', 'unknown').upper()
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f'{label} {confidence:.2f}'
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - 20)), (x1 + text_w + 6, max(20, y1)), (0, 255, 0), -1)
        cv2.putText(frame, text, (x1 + 3, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    inference_fps = 1000.0 / inference_time_ms if inference_time_ms > 0 else 0.0
    hud_lines = ['ELIOS-SAR ONBOARD AI', f'MODEL: {Path(MODEL_PATH).name}', f'INFERENCE: {inference_time_ms:.1f} ms', f'INFERENCE FPS: {inference_fps:.1f}', f'DETECTIONS: {len(detections)}']
    x = 10
    y = 25
    for index, line in enumerate(hud_lines):
        cv2.putText(frame, line, (x, y + index * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)
    return frame

def build_ai_message(detections, inference_time_ms):
    return {'type': 'PERSON_DETECTION', 'source': DRONE_ID, 'timestamp': datetime.now(timezone.utc).isoformat(), 'inference_time_ms': round(inference_time_ms, 2), 'inference_fps': round(1000.0 / inference_time_ms if inference_time_ms > 0 else 0.0, 2), 'detections': detections}

async def stream_pipeline():
    print('=' * 60)
    print('ELIOS-SAR ONBOARD AI + DUAL WEBSOCKET STREAMER')
    print('=' * 60)
    print(f'Model Path : {MODEL_PATH}')
    print(f'Camera     : {CAMERA_WIDTH}x{CAMERA_HEIGHT}@{CAMERA_FPS}')
    print(f'YOLO Conf  : {YOLO_CONFIDENCE}')
    print()
    camera = None
    detector = None
    video_ws = None
    ai_ws = None
    try:
        logger.info('Initializing camera...')
        camera = Camera(device=CAMERA_DEVICE, width=CAMERA_WIDTH, height=CAMERA_HEIGHT, fps=CAMERA_FPS)
        logger.info('Camera initialized successfully.')
        logger.info('Loading YOLO model: %s', MODEL_PATH)
        detector = RGBDetector(model_path=MODEL_PATH, confidence=YOLO_CONFIDENCE)
        logger.info('YOLO model loaded successfully.')
        video_ws = VideoWebSocketClient()
        ai_ws = AIWebSocketClient()
        logger.info('Connecting to GCS Video WebSocket...')
        await video_ws.connect()
        logger.info('Video WebSocket connected.')
        logger.info('Connecting to GCS AI WebSocket...')
        await ai_ws.connect()
        logger.info('AI WebSocket connected.')
        logger.info('Camera and AI dual-stream pipeline started.')
        logger.info('Press Ctrl+C to stop.')
        while True:
            frame = camera.read()
            if frame is None:
                continue
            inference_start = time.perf_counter()
            detections = detector.detect(frame)
            inference_end = time.perf_counter()
            inference_time_ms = (inference_end - inference_start) * 1000.0
            annotated = draw_detections(frame.copy(), detections, inference_time_ms)
            success, encoded = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not success:
                logger.warning('Failed to encode video frame.')
                continue
            jpeg_bytes = encoded.tobytes()
            await video_ws.send_frame(jpeg_bytes)
            message = build_ai_message(detections, inference_time_ms)
            await ai_ws.send(message)
            await asyncio.sleep(0.01)
    finally:
        if camera is not None:
            camera.release()
        if video_ws is not None:
            await video_ws.close()
        if ai_ws is not None:
            await ai_ws.close()
        logger.info('Pipeline stopped and resources released.')

def main():
    try:
        asyncio.run(stream_pipeline())
    except KeyboardInterrupt:
        print()
        logger.info('Stopped by user.')
    except Exception as error:
        logger.error('Pipeline runtime error: %s', error)
if __name__ == '__main__':
    main()
