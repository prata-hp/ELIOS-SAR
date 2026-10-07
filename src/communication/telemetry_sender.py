from __future__ import annotations
import asyncio
import json
import logging
import time
import websockets
logger = logging.getLogger('ELIOS.TelemetrySender')

class TelemetrySender:

    def __init__(self, gcs_host: str, port: int=8766, reconnect_delay: float=2.0):
        self.uri = f'ws://{gcs_host}:{port}'
        self.reconnect_delay = reconnect_delay
        self.websocket = None
        self.running = True

    async def connect(self):
        while self.running:
            try:
                self.websocket = await websockets.connect(self.uri, ping_interval=20, ping_timeout=20, max_size=4 * 1024 * 1024)
                logger.info('Connected to GCS telemetry: %s', self.uri)
                return True
            except Exception as exc:
                logger.warning('GCS telemetry connection failed: %s', exc)
                await asyncio.sleep(self.reconnect_delay)
        return False

    async def send(self, packet: dict):
        if self.websocket is None:
            connected = await self.connect()
            if not connected:
                return False
        try:
            await self.websocket.send(json.dumps(packet, separators=(',', ':')))
            return True
        except Exception as exc:
            logger.warning('Telemetry send failed: %s', exc)
            try:
                await self.websocket.close()
            except Exception:
                pass
            self.websocket = None
            return False

    async def close(self):
        self.running = False
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None
