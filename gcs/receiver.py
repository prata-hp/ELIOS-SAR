from __future__ import annotations
import asyncio
import json
import logging
import websockets
from gcs.processor import GCSProcessor
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('GCS.Receiver')

class GCSReceiver:

    def __init__(self, host='0.0.0.0', port=8766):
        self.host = host
        self.port = port
        self.processor = GCSProcessor()

    async def handler(self, websocket):
        logger.info('ELIOS connected from %s', websocket.remote_address)
        async for message in websocket:
            try:
                packet = json.loads(message)
                result = self.processor.process(packet)
                logger.info('DRONE=%s | RISK=%s | SCORE=%s | REASONS=%s', result['drone_id'], result['risk']['level'], result['risk']['score'], result['risk']['reasons'])
                if result['incident']:
                    logger.warning('INCIDENT=%s | LEVEL=%s', result['incident']['incident_id'], result['incident']['level'])
            except Exception as exc:
                logger.exception('Invalid telemetry packet: %s', exc)

    async def run(self):
        async with websockets.serve(self.handler, self.host, self.port, ping_interval=20, ping_timeout=20, max_size=4 * 1024 * 1024):
            logger.info('GCS telemetry receiver listening on %s:%s', self.host, self.port)
            await asyncio.Future()
if __name__ == '__main__':
    receiver = GCSReceiver()
    asyncio.run(receiver.run())
