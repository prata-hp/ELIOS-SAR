import asyncio
import json
import time
from typing import Dict, Any, Optional
import cv2
import numpy as np
import websockets
from gcs.annotation_renderer import AnnotationRenderer
VIDEO_HOST = '0.0.0.0'
VIDEO_PORT = 8766
DETECTION_HOST = '0.0.0.0'
DETECTION_PORT = 8767
WINDOW_NAME = 'ELIOS-SAR | GCS Annotated Intelligence Feed'

class GCSVideoReceiver:

    def __init__(self):
        self.renderer = AnnotationRenderer()
        self.latest_frames: Dict[int, np.ndarray] = {}
        self.latest_detections: Dict[int, Dict[str, Any]] = {}
        self.latest_frame: Optional[np.ndarray] = None
        self.latest_frame_id: int = -1
        self.latest_detection_packet: Dict[str, Any] = {}
        self.running = True

    async def video_handler(self, websocket):
        print('[GCS VIDEO] Client connected')
        try:
            async for message in websocket:
                if isinstance(message, str):
                    message = message.encode('latin1')
                try:
                    packet = json.loads(message.decode('utf-8'))
                except Exception:
                    print('[GCS VIDEO] Invalid JSON packet')
                    continue
                frame_id = int(packet['frame_id'])
                jpeg_data = packet['jpeg_data']
                if isinstance(jpeg_data, str):
                    import base64
                    jpeg_data = base64.b64decode(jpeg_data)
                array = np.frombuffer(jpeg_data, dtype=np.uint8)
                frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
                if frame is None:
                    print(f'[GCS VIDEO] Could not decode frame {frame_id}')
                    continue
                self.latest_frames[frame_id] = frame
                self.latest_frame = frame
                self.latest_frame_id = frame_id
                if len(self.latest_frames) > 100:
                    oldest = sorted(self.latest_frames.keys())[0]
                    del self.latest_frames[oldest]
                self.try_render(frame_id)
        except websockets.exceptions.ConnectionClosed:
            print('[GCS VIDEO] Client disconnected')
        except Exception as exc:
            print(f'[GCS VIDEO] Error: {exc}')

    async def detection_handler(self, websocket):
        print('[GCS DETECTIONS] Client connected')
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                try:
                    packet = json.loads(message)
                except Exception:
                    print('[GCS DETECTIONS] Invalid JSON')
                    continue
                frame_id = int(packet['frame_id'])
                self.latest_detections[frame_id] = packet
                self.latest_detection_packet = packet
                if len(self.latest_detections) > 100:
                    oldest = sorted(self.latest_detections.keys())[0]
                    del self.latest_detections[oldest]
                self.try_render(frame_id)
        except websockets.exceptions.ConnectionClosed:
            print('[GCS DETECTIONS] Client disconnected')
        except Exception as exc:
            print(f'[GCS DETECTIONS] Error: {exc}')

    def try_render(self, frame_id: int):
        if frame_id not in self.latest_frames:
            return
        if frame_id not in self.latest_detections:
            frame = self.latest_frames[frame_id]
            cv2.imshow(WINDOW_NAME, frame)
            cv2.waitKey(1)
            return
        frame = self.latest_frames[frame_id]
        detection_packet = self.latest_detections[frame_id]
        detections = detection_packet.get('detections', [])
        risk_level = detection_packet.get('risk_level', 'UNKNOWN')
        risk_score = float(detection_packet.get('risk_score', 0))
        timestamp = float(detection_packet.get('timestamp', time.time()))
        annotated = self.renderer.render(frame=frame, detections=detections, risk_level=risk_level, risk_score=risk_score, frame_id=frame_id, timestamp=timestamp)
        cv2.imshow(WINDOW_NAME, annotated)
        key = cv2.waitKey(1) & 255
        if key == ord('q'):
            self.running = False

    async def run(self):
        print('=' * 70)
        print('ELIOS-SAR GCS VIDEO + AI ANNOTATION RECEIVER')
        print('=' * 70)
        print(f'Video WebSocket:      ws://0.0.0.0:{VIDEO_PORT}')
        print(f'Detection WebSocket:  ws://0.0.0.0:{DETECTION_PORT}')
        print('Press Q in the video window to stop')
        print('=' * 70)
        video_server = await websockets.serve(self.video_handler, VIDEO_HOST, VIDEO_PORT, max_size=8 * 1024 * 1024)
        detection_server = await websockets.serve(self.detection_handler, DETECTION_HOST, DETECTION_PORT, max_size=2 * 1024 * 1024)
        print('[GCS] Both servers started')
        try:
            while self.running:
                await asyncio.sleep(0.1)
        finally:
            video_server.close()
            detection_server.close()
            await video_server.wait_closed()
            await detection_server.wait_closed()
            cv2.destroyAllWindows()
            print('[GCS] Servers stopped')
if __name__ == '__main__':
    receiver = GCSVideoReceiver()
    asyncio.run(receiver.run())
