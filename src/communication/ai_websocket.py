from __future__ import annotations
import asyncio
import json
import logging
import websockets
from drone.config import AI_WS_URL
logger = logging.getLogger(__name__)

class AIWebSocketClient:

    def __init__(self):
        self.url = AI_WS_URL
        self.websocket = None

    async def connect(self):
        while True:
            try:
                logger.info('Connecting to AI WebSocket: %s', self.url)
                self.websocket = await websockets.connect(self.url, ping_interval=20, ping_timeout=20, max_size=1024 * 1024)
                logger.info('AI WebSocket connected')
                return
            except Exception as exc:
                logger.warning('AI WebSocket connection failed: %s', exc)
                await asyncio.sleep(2)

    async def send(self, message):
        if self.websocket is None:
            await self.connect()
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as exc:
            logger.warning('AI WebSocket send failed: %s', exc)
            self.websocket = None
            await self.connect()
            await self.websocket.send(json.dumps(message))

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
