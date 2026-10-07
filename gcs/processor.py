from __future__ import annotations
from gcs.telemetry_schema import validate_observation
from gcs.coordinate_validator import validate_drone_pose
from gcs.detection_tracker import DetectionTracker
from gcs.risk_assessment import GCSRiskAssessment
from gcs.incident_manager import IncidentManager
from gcs.mapping_engine import MappingEngine

class GCSProcessor:

    def __init__(self):
        self.tracker = DetectionTracker()
        self.risk_engine = GCSRiskAssessment()
        self.incident_manager = IncidentManager()
        self.mapping_engine = MappingEngine()

    def process(self, raw_packet: dict) -> dict:
        packet = validate_observation(raw_packet)
        validated_pose = validate_drone_pose(packet.get('drone_pose'))
        all_detections = []
        all_detections.extend(packet.get('persons', []))
        for hazard_type, hazard_items in packet.get('hazards', {}).items():
            for hazard in hazard_items:
                item = dict(hazard)
                item['hazard_type'] = hazard_type
                all_detections.append(item)
        tracked = self.tracker.update(all_detections)
        persons = [item for item in tracked if item.get('hazard_type') is None]
        hazards = {}
        for item in tracked:
            hazard_type = item.get('hazard_type')
            if hazard_type is not None:
                hazards.setdefault(hazard_type, []).append(item)
        normalized_packet = dict(packet)
        normalized_packet['persons'] = persons
        normalized_packet['hazards'] = hazards
        risk = self.risk_engine.evaluate(normalized_packet)
        incident = self.incident_manager.update(drone_id=packet['drone_id'], level=risk.level, score=risk.score, reasons=risk.reasons)
        map_observation = self.mapping_engine.add_packet(normalized_packet, validated_pose)
        return {'drone_id': packet['drone_id'], 'timestamp': packet['timestamp'], 'risk': {'score': risk.score, 'level': risk.level, 'reasons': risk.reasons}, 'incident': {'incident_id': incident.incident_id, 'level': incident.level, 'active': incident.active, 'observations': incident.observations} if incident else None, 'pose': {'valid': validated_pose.valid, 'frame': validated_pose.frame, 'x': validated_pose.x, 'y': validated_pose.y, 'z': validated_pose.z, 'reason': validated_pose.reason}, 'tracked_detections': tracked, 'mapping': {'object_coordinates_available': False, 'reason': 'Object coordinates require depth, stereo, LiDAR, or geometric reconstruction.'}}
