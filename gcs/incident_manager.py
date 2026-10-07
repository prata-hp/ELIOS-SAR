from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field

@dataclass
class Incident:
    incident_id: str
    drone_id: str
    level: str
    score: int
    reasons: list[str]
    first_seen: float
    last_seen: float
    active: bool = True
    observations: int = 1

class IncidentManager:

    def __init__(self):
        self.active_incidents: dict[str, Incident] = {}

    def update(self, drone_id: str, level: str, score: int, reasons: list[str]) -> Incident | None:
        if level not in {'HIGH', 'CRITICAL'}:
            return None
        now = time.time()
        key = drone_id
        if key in self.active_incidents:
            incident = self.active_incidents[key]
            incident.level = level
            incident.score = score
            incident.reasons = reasons
            incident.last_seen = now
            incident.observations += 1
            return incident
        incident = Incident(incident_id=str(uuid.uuid4()), drone_id=drone_id, level=level, score=score, reasons=reasons, first_seen=now, last_seen=now)
        self.active_incidents[key] = incident
        return incident

    def clear_stale(self, timeout: float=10.0):
        now = time.time()
        stale = [drone_id for drone_id, incident in self.active_incidents.items() if now - incident.last_seen > timeout]
        for drone_id in stale:
            self.active_incidents[drone_id].active = False
            del self.active_incidents[drone_id]
