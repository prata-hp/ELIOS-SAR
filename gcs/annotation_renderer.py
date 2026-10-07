import cv2
import numpy as np
from typing import Dict, Any, List

class AnnotationRenderer:

    def __init__(self):
        self.class_display_names = {'person': 'PERSON', 'rescuer': 'RESCUER', 'civilian': 'CIVILIAN', 'fire': 'FIRE', 'smoke': 'SMOKE', 'water': 'FLOOD/WATER', 'rock': 'BOULDER', 'boulder': 'BOULDER', 'unknown': 'UNKNOWN'}

    def _get_color(self, class_name: str):
        colors = {'person': (0, 255, 0), 'rescuer': (255, 255, 0), 'civilian': (0, 255, 0), 'fire': (0, 0, 255), 'smoke': (128, 128, 128), 'water': (255, 0, 0), 'rock': (42, 42, 165), 'boulder': (42, 42, 165), 'unknown': (255, 255, 255)}
        return colors.get(class_name.lower(), (255, 255, 255))

    def _draw_text(self, frame, text, position, color=(255, 255, 255), scale=0.55, thickness=1):
        x, y = position
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
        cv2.rectangle(frame, (x, y - text_height - baseline - 4), (x + text_width + 4, y), (0, 0, 0), -1)
        cv2.putText(frame, text, (x + 2, y - 3), font, scale, color, thickness, cv2.LINE_AA)

    def render(self, frame: np.ndarray, detections: List[Dict[str, Any]], risk_level: str='UNKNOWN', risk_score: float=0, frame_id: int=0, timestamp: float=0) -> np.ndarray:
        output = frame.copy()
        for detection in detections:
            class_name = str(detection.get('class_name', 'unknown')).lower()
            confidence = float(detection.get('confidence', 0.0))
            bbox = detection.get('bbox')
            if not bbox or len(bbox) != 4:
                continue
            x1, y1, x2, y2 = map(int, bbox)
            color = self._get_color(class_name)
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(output.shape[1] - 1, x2)
            y2 = min(output.shape[0] - 1, y2)
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            label = self.class_display_names.get(class_name, class_name.upper())
            label += f' {confidence:.2f}'
            track_id = detection.get('track_id')
            if track_id is not None:
                label += f' ID:{track_id}'
            self._draw_text(output, label, (x1, max(y1, 25)), color=color, scale=0.55, thickness=1)
        panel_height = 70
        overlay = output.copy()
        cv2.rectangle(overlay, (0, 0), (output.shape[1], panel_height), (0, 0, 0), -1)
        output = cv2.addWeighted(overlay, 0.65, output, 0.35, 0)
        risk_color = {'LOW': (0, 255, 0), 'MEDIUM': (0, 255, 255), 'HIGH': (0, 165, 255), 'CRITICAL': (0, 0, 255), 'UNKNOWN': (255, 255, 255)}.get(risk_level.upper(), (255, 255, 255))
        cv2.putText(output, 'ELIOS-SAR | GCS INTELLIGENCE FEED', (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(output, f'RISK: {risk_level} | SCORE: {risk_score:.1f}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, risk_color, 2, cv2.LINE_AA)
        cv2.putText(output, f'FRAME: {frame_id}', (output.shape[1] - 180, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(output, f'DETECTIONS: {len(detections)}', (output.shape[1] - 180, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return output
