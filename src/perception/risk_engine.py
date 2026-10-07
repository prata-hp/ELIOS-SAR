from dataclasses import dataclass
import time

@dataclass
class RiskResult:
    score: int
    level: str
    reasons: list[str]

class RiskEngine:

    def __init__(self):
        self.last_event_time = {}

    def evaluate(self, persons=None, poses=None, hazards=None, gas_state=None) -> RiskResult:
        persons = persons or []
        poses = poses or []
        hazards = hazards or {}
        score = 0
        reasons = []
        if persons:
            score += 40
            reasons.append('person_detected')
        for pose in poses:
            posture = getattr(pose, 'posture', '')
            if posture in {'lying', 'fallen'}:
                score += 30
                reasons.append('possible_immobile_person')
                break
        fire_detections = hazards.get('fire', [])
        if fire_detections:
            score += 30
            reasons.append('fire_detected')
        flood_detections = hazards.get('flood', [])
        if flood_detections:
            max_flood_score = 20
            for detection in flood_detections:
                severity = getattr(detection, 'severity', None)
                if isinstance(detection, dict):
                    severity = detection.get('severity', severity)
                severity = str(severity or 'low').lower()
                if severity == 'critical':
                    max_flood_score = max(max_flood_score, 50)
                elif severity == 'high':
                    max_flood_score = max(max_flood_score, 35)
                elif severity == 'medium':
                    max_flood_score = max(max_flood_score, 25)
            score += max_flood_score
            reasons.append('flood_detected')
        boulder_detections = hazards.get('boulder', [])
        for detection in boulder_detections:
            if isinstance(detection, dict):
                obstruction_level = detection.get('obstruction_level', detection.get('severity', 'low'))
            else:
                obstruction_level = getattr(detection, 'obstruction_level', getattr(detection, 'severity', 'low'))
            obstruction_level = str(obstruction_level).lower()
            if obstruction_level == 'critical':
                score += 40
                reasons.append('critical_path_obstruction')
            elif obstruction_level == 'high':
                score += 25
                reasons.append('high_path_obstruction')
            elif obstruction_level in {'medium', 'moderate'}:
                score += 10
                reasons.append('medium_path_obstruction')
        if gas_state:
            gas_state = str(gas_state).lower()
            if gas_state == 'critical':
                score += 50
                reasons.append('critical_gas')
            elif gas_state == 'dangerous':
                score += 30
                reasons.append('dangerous_gas')
            elif gas_state == 'elevated':
                score += 10
                reasons.append('elevated_gas')
        if score >= 70:
            level = 'CRITICAL'
        elif score >= 40:
            level = 'HIGH'
        elif score >= 20:
            level = 'MEDIUM'
        else:
            level = 'LOW'
        return RiskResult(score=score, level=level, reasons=reasons)

    def should_emit(self, event_key: str, cooldown: float=2.0):
        now = time.monotonic()
        previous = self.last_event_time.get(event_key, 0.0)
        if now - previous < cooldown:
            return False
        self.last_event_time[event_key] = now
        return True
