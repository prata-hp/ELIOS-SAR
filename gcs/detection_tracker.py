from __future__ import annotations
import math
import time
from dataclasses import dataclass

@dataclass
class Track:
    track_id: int
    label: str
    cx: float
    cy: float
    confidence: float
    last_seen: float

class DetectionTracker:

    def __init__(self, distance_threshold: float=80.0):
        self.distance_threshold = distance_threshold
        self.next_track_id = 1
        self.tracks: list[Track] = []

    def _distance(self, a, b):
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def update(self, detections: list[dict]) -> list[dict]:
        now = time.time()
        output = []
        used_tracks = set()
        for detection in detections:
            bbox = detection.get('bbox')
            if not bbox or len(bbox) != 4:
                detection['track_id'] = None
                output.append(detection)
                continue
            x1, y1, x2, y2 = bbox
            center = ((float(x1) + float(x2)) / 2.0, (float(y1) + float(y2)) / 2.0)
            label = str(detection.get('class', detection.get('label', 'unknown')))
            best_track = None
            best_distance = float('inf')
            for track in self.tracks:
                if track.track_id in used_tracks:
                    continue
                if track.label != label:
                    continue
                distance = self._distance(center, (track.cx, track.cy))
                if distance < self.distance_threshold and distance < best_distance:
                    best_track = track
                    best_distance = distance
            if best_track is None:
                best_track = Track(track_id=self.next_track_id, label=label, cx=center[0], cy=center[1], confidence=float(detection.get('confidence', 0.0)), last_seen=now)
                self.next_track_id += 1
                self.tracks.append(best_track)
            else:
                best_track.cx = center[0]
                best_track.cy = center[1]
                best_track.confidence = float(detection.get('confidence', 0.0))
                best_track.last_seen = now
            used_tracks.add(best_track.track_id)
            detection['track_id'] = best_track.track_id
            output.append(detection)
        self.tracks = [track for track in self.tracks if now - track.last_seen < 2.0]
        return output
