from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidatedPose:
    valid: bool
    frame: str
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    roll: Optional[float]
    pitch: Optional[float]
    yaw: Optional[float]
    reason: str = ''

def validate_drone_pose(pose: dict | None) -> ValidatedPose:
    if pose is None:
        return ValidatedPose(valid=False, frame='unknown', x=None, y=None, z=None, roll=None, pitch=None, yaw=None, reason='pose_unavailable')
    frame = str(pose.get('frame', 'unknown'))
    required = ['x', 'y', 'z']
    for field in required:
        if field not in pose:
            return ValidatedPose(valid=False, frame=frame, x=None, y=None, z=None, roll=None, pitch=None, yaw=None, reason=f'missing_{field}')
    try:
        x = float(pose['x'])
        y = float(pose['y'])
        z = float(pose['z'])
        roll = float(pose.get('roll', 0.0))
        pitch = float(pose.get('pitch', 0.0))
        yaw = float(pose.get('yaw', 0.0))
    except (TypeError, ValueError):
        return ValidatedPose(valid=False, frame=frame, x=None, y=None, z=None, roll=None, pitch=None, yaw=None, reason='non_numeric_pose')
    values = [x, y, z, roll, pitch, yaw]
    for value in values:
        if value != value:
            return ValidatedPose(valid=False, frame=frame, x=None, y=None, z=None, roll=None, pitch=None, yaw=None, reason='nan_pose')
    return ValidatedPose(valid=True, frame=frame, x=x, y=y, z=z, roll=roll, pitch=pitch, yaw=yaw, reason='valid')
