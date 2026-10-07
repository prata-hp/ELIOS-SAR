import asyncio
import base64
import json
import time
from typing import Optional
import cv2
import websockets

class VideoSender:

    def __init__(self, gcs_host: str, video_port: int=8766, detection_port: int=8767, jpeg_quality: int=75):
        self.gcs_host = gcs_host
        self.video_port = video_port
        self.detection_port = detection_port
        self.jpeg_quality = jpeg_quality
        self.video_ws = None
        self.detection_ws = None

    async def connect(self):
        video_uri = f'ws://{self.gcs_host}:{self.video_port}'
        detection_uri = f'ws://{self.gcs_host}:{self.detection_port}'
        self.video_ws = await websockets.connect(video_uri, max_size=8 * 1024 * 1024, ping_interval=20, ping_timeout=20)
        self.detection_ws = await websockets.connect(detection_uri, max_size=2 * 1024 * 1024, ping_interval=20, ping_timeout=20)
        print('[ELIOS VIDEO] Connected to GCS video channel')
        print('[ELIOS VIDEO] Connected to GCS detection channel')

    async def send(self, frame, frame_id: int, detections, risk_level: str='UNKNOWN', risk_score: float=0, timestamp: Optional[float]=None):
        if timestamp is None:
            timestamp = time.time()
        if self.video_ws is None or self.detection_ws is None:
            await self.connect()
        success, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        if not success:
            print('[ELIOS VIDEO] JPEG encoding failed')
            return
        jpeg_bytes = encoded.tobytes()
        video_packet = {'frame_id': frame_id, 'timestamp': timestamp, 'jpeg_data': base64.b64encode(jpeg_bytes).decode('ascii')}
        detection_packet = {'frame_id': frame_id, 'timestamp': timestamp, 'detections': detections, 'risk_level': risk_level, 'risk_score': risk_score}
        try:
            await self.video_ws.send(json.dumps(video_packet))
            await self.detection_ws.send(json.dumps(detection_packet))
        except Exception as exc:
            print(f'[ELIOS VIDEO] Send error: {exc}')
            try:
                if self.video_ws:
                    await self.video_ws.close()
                if self.detection_ws:
                    await self.detection_ws.close()
            except Exception:
                pass
            self.video_ws = None
            self.detection_ws = None

    async def close(self):
        if self.video_ws is not None:
            await self.video_ws.close()
        if self.detection_ws is not None:
            await self.detection_ws.close()
        self.video_ws = None
        self.detection_ws = None
