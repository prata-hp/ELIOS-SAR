from __future__ import annotations
from dataclasses import dataclass

@dataclass
class GCSRiskResult:
    score: int
    level: str
    reasons: list[str]

class GCSRiskAssessment:

    def evaluate(self, packet: dict) -> GCSRiskResult:
        score = 0
        reasons = []
        persons = packet.get('persons', [])
        hazards = packet.get('hazards', {})
        sensors = packet.get('sensors', {})
        if persons:
            score += 35
            reasons.append('person_detected')
        for person in persons:
            posture = str(person.get('posture', '')).lower()
            if posture in {'lying', 'fallen', 'immobile'}:
                score += 35
                reasons.append('possible_immobile_person')
                break
        fire = hazards.get('fire', [])
        if fire:
            score += 35
            reasons.append('fire_detected')
        flood = hazards.get('flood', [])
        if flood:
            score += 25
            reasons.append('flood_detected')
            for item in flood:
                severity = str(item.get('severity', 'low')).lower()
                if severity == 'critical':
                    score += 25
                elif severity == 'high':
                    score += 15
        boulders = hazards.get('boulder', [])
        for item in boulders:
            obstruction = str(item.get('obstruction_level', item.get('severity', 'low'))).lower()
            if obstruction == 'critical':
                score += 40
                reasons.append('critical_path_obstruction')
            elif obstruction == 'high':
                score += 25
                reasons.append('high_path_obstruction')
            elif obstruction in {'medium', 'moderate'}:
                score += 10
                reasons.append('medium_path_obstruction')
        gas_level = str(sensors.get('gas_level', 'normal')).lower()
        if gas_level == 'critical':
            score += 50
            reasons.append('critical_gas')
        elif gas_level == 'dangerous':
            score += 30
            reasons.append('dangerous_gas')
        elif gas_level == 'elevated':
            score += 10
            reasons.append('elevated_gas')
        if score >= 80:
            level = 'CRITICAL'
        elif score >= 50:
            level = 'HIGH'
        elif score >= 20:
            level = 'MEDIUM'
        else:
            level = 'LOW'
        return GCSRiskResult(score=min(score, 100), level=level, reasons=reasons)
