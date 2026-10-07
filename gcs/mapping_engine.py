from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class MapObservation:
    timestamp: float
    drone_id: str
    pose_valid: bool
    frame: str
    drone_position: dict | None
    detections: list[dict]
    object_coordinates_available: bool = False

class MappingEngine:

    def __init__(self):
        self.observations: list[MapObservation] = []

    def add_packet(self, packet: dict, validated_pose) -> MapObservation:
        drone_position = None
        if validated_pose.valid:
            drone_position = {'x': validated_pose.x, 'y': validated_pose.y, 'z': validated_pose.z, 'roll': validated_pose.roll, 'pitch': validated_pose.pitch, 'yaw': validated_pose.yaw}
        detections = []
        for person in packet.get('persons', []):
            item = dict(person)
            item['world_coordinates'] = None
            item['coordinates_status'] = 'unavailable_without_depth_or_geometry'
            detections.append(item)
        for hazard_type, hazard_items in packet.get('hazards', {}).items():
            for hazard in hazard_items:
                item = dict(hazard)
                item['hazard_type'] = hazard_type
                item['world_coordinates'] = None
                item['coordinates_status'] = 'unavailable_without_depth_or_geometry'
                detections.append(item)
        observation = MapObservation(timestamp=float(packet['timestamp']), drone_id=packet['drone_id'], pose_valid=validated_pose.valid, frame=validated_pose.frame, drone_position=drone_position, detections=detections)
        self.observations.append(observation)
        if len(self.observations) > 10000:
            self.observations = self.observations[-10000:]
        return observation

    def export(self) -> list[dict]:
        return [asdict(observation) for observation in self.observations]
