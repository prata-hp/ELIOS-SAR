from __future__ import annotations
from typing import Any

class TelemetryValidationError(ValueError):
    pass

def _require(data: dict, key: str):
    if key not in data:
        raise TelemetryValidationError(f'Missing required telemetry field: {key}')

def validate_observation(packet: dict) -> dict:
    if not isinstance(packet, dict):
        raise TelemetryValidationError('Telemetry packet must be a dictionary')
    _require(packet, 'type')
    _require(packet, 'drone_id')
    _require(packet, 'timestamp')
    if packet['type'] != 'ai_observation':
        raise TelemetryValidationError(f"Unsupported packet type: {packet['type']}")
    if not isinstance(packet['drone_id'], str):
        raise TelemetryValidationError('drone_id must be a string')
    if not isinstance(packet['timestamp'], (int, float)):
        raise TelemetryValidationError('timestamp must be numeric')
    persons = packet.get('persons', [])
    hazards = packet.get('hazards', {})
    pose = packet.get('drone_pose')
    sensors = packet.get('sensors', {})
    risk = packet.get('risk', {})
    if not isinstance(persons, list):
        raise TelemetryValidationError('persons must be a list')
    if not isinstance(hazards, dict):
        raise TelemetryValidationError('hazards must be a dictionary')
    if pose is not None and (not isinstance(pose, dict)):
        raise TelemetryValidationError('drone_pose must be an object or null')
    if not isinstance(sensors, dict):
        raise TelemetryValidationError('sensors must be a dictionary')
    if not isinstance(risk, dict):
        raise TelemetryValidationError('risk must be a dictionary')
    return {'type': packet['type'], 'drone_id': packet['drone_id'], 'timestamp': packet['timestamp'], 'persons': persons, 'hazards': hazards, 'drone_pose': pose, 'sensors': sensors, 'risk': risk, 'frame_id': packet.get('frame_id'), 'source': packet.get('source', 'ELIOS')}
