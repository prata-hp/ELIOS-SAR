from __future__ import annotations
import asyncio
import logging
import websockets
from drone.config import VIDEO_WS_URL
logger = logging.getLogger(__name__)

class VideoWebSocketClient:

    def __init__(self):
        self.url = VIDEO_WS_URL
        self.websocket = None

    async def connect(self):
        while True:
            try:
                logger.info('Connecting to Video WebSocket: %s', self.url)
                self.websocket = await websockets.connect(self.url, ping_interval=20, ping_timeout=20, max_size=2 * 1024 * 1024)
                logger.info('Video WebSocket connected')
                return
            except Exception as exc:
                logger.warning('Video WebSocket connection failed: %s', exc)
                await asyncio.sleep(2)

    async def send_frame(self, jpeg_bytes: bytes):
        if self.websocket is None:
            await self.connect()
        try:
            await self.websocket.send(jpeg_bytes)
        except Exception as exc:
            logger.warning('Video WebSocket send failed: %s', exc)
            self.websocket = None
            await self.connect()
            await self.websocket.send(jpeg_bytes)

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
