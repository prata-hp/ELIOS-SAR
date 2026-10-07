from __future__ import annotations
from pathlib import Path
import sys
import time
import cv2
import asyncio
import os
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.telemetry.observation_serializer import ObservationSerializer
from src.communication.telemetry_sender import TelemetrySender
from src.localization.vio_provider import VIOProvider
from drone.config import MODEL_PATH, YOLO_CONFIDENCE, POSE_MODEL_PATH, POSE_CONFIDENCE, POSE_IMAGE_SIZE, POSE_INTERVAL_FRAMES, FIRE_MODEL_PATH, FLOOD_MODEL_PATH, BOULDER_MODEL_PATH, FIRE_CONFIDENCE, FLOOD_CONFIDENCE, BOULDER_CONFIDENCE, HAZARD_IMAGE_SIZE, BOULDER_IMAGE_SIZE, FIRE_INTERVAL_FRAMES, FLOOD_INTERVAL_FRAMES, BOULDER_INTERVAL_FRAMES, ENABLE_FIRE, ENABLE_FLOOD, ENABLE_BOULDER, ENABLE_POSE, RISK_EVENT_COOLDOWN_SECONDS, DRONE_ID
from src.perception.rgb_detector import RGBDetector
from src.perception.pose_estimator import PoseEstimator
from src.perception.hazard_detector import HazardDetector
from src.perception.boulder_detector import BoulderDetector
from src.perception.ai_scheduler import AIScheduler
from src.perception.risk_engine import RiskEngine
from src.perception.perception_pipeline import PerceptionPipeline
from src.perception.hardened_pipeline import HardenedPipeline
from src.core.risk_state import PersistentRiskState
from src.core.safe_emitter import SafeEventEmitter
from src.monitoring.metrics_writer import MetricsWriter
from src.testing.replay_writer import ReplayWriter
from src.communication.telemetry_queue import TelemetryQueue

def build_pipeline():
    print('[INIT] Loading person detector...')
    person_detector = RGBDetector(model_path=MODEL_PATH, confidence=YOLO_CONFIDENCE)
    pose_estimator = None
    if ENABLE_POSE:
        print('[INIT] Loading pose estimator...')
        pose_estimator = PoseEstimator(model_path=POSE_MODEL_PATH, confidence=POSE_CONFIDENCE, image_size=POSE_IMAGE_SIZE)
    fire_detector = None
    flood_detector = None
    boulder_detector = None
    if ENABLE_FIRE:
        print('[INIT] Loading fire detector...')
        fire_detector = HazardDetector(model_path=FIRE_MODEL_PATH, hazard_type='fire', confidence=FIRE_CONFIDENCE, image_size=HAZARD_IMAGE_SIZE)
    if ENABLE_FLOOD:
        print('[INIT] Loading flood detector...')
        flood_detector = HazardDetector(model_path=FLOOD_MODEL_PATH, hazard_type='flood', confidence=FLOOD_CONFIDENCE, image_size=HAZARD_IMAGE_SIZE)
    if ENABLE_BOULDER:
        print('[INIT] Loading boulder detector...')
        boulder_detector = BoulderDetector(model_path=BOULDER_MODEL_PATH, confidence=BOULDER_CONFIDENCE, image_size=BOULDER_IMAGE_SIZE)
    scheduler = AIScheduler(fire_detector=fire_detector, flood_detector=flood_detector, boulder_detector=boulder_detector, fire_interval=FIRE_INTERVAL_FRAMES, flood_interval=FLOOD_INTERVAL_FRAMES, boulder_interval=BOULDER_INTERVAL_FRAMES)
    base_pipeline = PerceptionPipeline(person_detector=person_detector, pose_estimator=pose_estimator, scheduler=scheduler, risk_engine=RiskEngine(), pose_interval=POSE_INTERVAL_FRAMES)
    hardened_pipeline = HardenedPipeline(base_pipeline=base_pipeline, person_confirm_hits=3, person_clear_misses=5, event_cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS)
    print('[INIT] Hardened pipeline initialized')
    return hardened_pipeline

def draw_results(frame, result, persistent_risk):
    output = frame.copy()
    for person in result.get('persons', []):
        bbox = person.get('bbox', [])
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            confirmed = person.get('confirmed', False)
            color = (0, 255, 0) if confirmed else (0, 200, 200)
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            label = f"{person.get('label', 'PERSON').upper()} {person.get('confidence', 0):.2f}"
            if confirmed:
                label += ' [CONFIRMED]'
            cv2.putText(output, label, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    hazards = result.get('hazards', {})
    if isinstance(hazards, dict):
        for hazard_type, detections in hazards.items():
            for detection in detections:
                bbox = detection.get('bbox', []) if isinstance(detection, dict) else getattr(detection, 'bbox', [])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = map(int, bbox)
                    cv2.rectangle(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    confidence = float(detection.get('confidence', 0.0) if isinstance(detection, dict) else getattr(detection, 'confidence', 0.0))
                    text = f'{hazard_type.upper()} {confidence:.2f}'
                    cv2.putText(output, text, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    if persistent_risk:
        level = getattr(persistent_risk, 'level', 'LOW')
        score = getattr(persistent_risk, 'score', 0.0)
        risk_color = (0, 255, 0)
        if level == 'MEDIUM':
            risk_color = (0, 165, 255)
        elif level in ('HIGH', 'CRITICAL'):
            risk_color = (0, 0, 255)
        cv2.putText(output, f'RISK: {level} | SCORE: {score:.2f}', (20, output.shape[0] - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.75, risk_color, 2)
    cv2.putText(output, f"Frame: {result.get('frame_id', 0)}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(output, f"Inference: {result.get('inference_ms', 0.0):.1f} ms", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return output

def main():
    video_path = ROOT / 'test.mp4'
    output_path = ROOT / 'recordings' / 'test_output.mp4'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print('=' * 70)
    print('ELIOS-SAR MP4 FULL PIPELINE TEST')
    print('=' * 70)
    print(f'[VIDEO] Input : {video_path}')
    print(f'[VIDEO] Output: {output_path}')
    if not video_path.exists():
        print(f'[ERROR] File not found: {video_path}')
        return 1
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print('[ERROR] Could not open test.mp4')
        return 1
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if source_fps <= 0:
        source_fps = 25.0
    print(f'[VIDEO] Resolution: {width}x{height}')
    print(f'[VIDEO] FPS: {source_fps:.2f}')
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*'mp4v'), source_fps, (width, height))
    if not writer.isOpened():
        print('[ERROR] Could not create output video')
        cap.release()
        return 1
    pipeline = build_pipeline()
    risk_manager = PersistentRiskState(promote_hits=3, demote_hits=5, smoothing_alpha=0.35)

    def sender(event):
        print(f"[EVENT] {event.get('event_type')} {event.get('payload', {})}")
    telemetry_queue = TelemetryQueue(sender=sender, max_size=100)
    telemetry_queue.start()
    emitter = SafeEventEmitter(sender=lambda event: telemetry_queue.put(event), cooldown_seconds=RISK_EVENT_COOLDOWN_SECONDS)
    drone_id = os.getenv('DRONE_ID', 'ELIOS-01')
    gcs_host = os.getenv('GCS_HOST', '127.0.0.1')
    telemetry_serializer = ObservationSerializer(drone_id=drone_id)
    telemetry_sender = TelemetrySender(gcs_host=gcs_host, port=int(os.getenv('AI_WS_PORT', '8766')))
    vio_provider = VIOProvider()
    telemetry_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(telemetry_loop)
    metrics_writer = MetricsWriter(path='logs/mp4_metrics.jsonl')
    replay_writer = ReplayWriter(path='recordings/mp4_replay.jsonl')
    frame_count = 0
    start_time = time.perf_counter()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1
            frame_start = time.perf_counter()
            result = pipeline.process(frame)
            raw_risk = result.get('risk')
            if raw_risk:
                level = getattr(raw_risk, 'level', None)
                score = getattr(raw_risk, 'score', None)
                if isinstance(raw_risk, dict):
                    level = raw_risk.get('level', 'LOW')
                    score = raw_risk.get('score', 0.0)
                persistent_risk = risk_manager.update(level or 'LOW', score or 0.0)
            else:
                persistent_risk = risk_manager.update('LOW', 0.0)
            result['persistent_risk'] = risk_manager.snapshot()
            confirmed_persons = result.get('confirmed_persons', [])
            for person in confirmed_persons:
                confidence = float(person.get('confidence', 0.0) if isinstance(person, dict) else getattr(person, 'confidence', 0.0))
                bbox = person.get('bbox', []) if isinstance(person, dict) else getattr(person, 'bbox', [])
                emitter.emit(event_type='person_detected', source='person_model', drone_id=DRONE_ID, confidence=confidence, bbox=bbox)
            hazards = result.get('hazards', {})
            if isinstance(hazards, dict):
                for hazard_type, detections in hazards.items():
                    for detection in detections:
                        if isinstance(detection, dict):
                            payload = detection.copy()
                            payload.pop('mask', None)
                        else:
                            payload = {key: value for key, value in vars(detection).items() if key != 'mask'}
                        if hazard_type == 'boulder':
                            event_type = 'obstruction_detected'
                            source = 'boulder_segmentation'
                        elif hazard_type == 'flood':
                            event_type = 'flood_detected'
                            source = 'flood_segmentation'
                        elif hazard_type == 'fire':
                            event_type = 'fire_detected'
                            source = 'fire_model'
                        else:
                            event_type = f'{hazard_type}_detected'
                            source = f'{hazard_type}_model'
                        emitter.emit(event_type=event_type, source=source, drone_id=DRONE_ID, **payload)
            frame_id = result.get('frame_id', frame_count)
            replay_writer.write(frame_id, result)
            telemetry_packet = telemetry_serializer.build(persons=result.get('persons', []), hazards=result.get('hazards', {}), drone_pose=vio_provider.get_pose(), sensors={}, risk={'score': getattr(persistent_risk, 'score', 0), 'level': getattr(persistent_risk, 'level', 'LOW'), 'reasons': getattr(persistent_risk, 'reasons', [])})
            try:
                telemetry_loop.run_until_complete(telemetry_sender.send(telemetry_packet))
            except Exception:
                pass
            if frame_count % 15 == 0:
                elapsed = time.perf_counter() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0.0
                metrics_writer.write({'frame_id': frame_id, 'fps': fps, 'inference_ms': (time.perf_counter() - frame_start) * 1000, 'risk_level': persistent_risk.level, 'risk_score': persistent_risk.score, 'person_count': len(result.get('persons', [])), 'confirmed_person_count': len(confirmed_persons), 'queue_size': telemetry_queue.queue.qsize()})
            annotated = draw_results(frame, result, persistent_risk)
            writer.write(annotated)
            cv2.imshow('ELIOS-SAR MP4 Full Pipeline Test', annotated)
            key = cv2.waitKey(1) & 255
            if key in (ord('q'), 27):
                print('[INFO] Stopped by user')
                break
            if frame_count % 30 == 0:
                elapsed = time.perf_counter() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0.0
                print(f"[PROGRESS] Frames={frame_count} FPS={fps:.2f} Persons={len(result.get('persons', []))} Confirmed={len(confirmed_persons)} Risk={persistent_risk.level}")
    except KeyboardInterrupt:
        print('[INFO] Interrupted by user')
    finally:
        try:
            telemetry_loop.run_until_complete(telemetry_sender.close())
            telemetry_loop.close()
        except Exception:
            pass
        cap.release()
        writer.release()
        cv2.destroyAllWindows()
        try:
            telemetry_queue.stop()
        except Exception:
            pass
        elapsed = time.perf_counter() - start_time
        print()
        print('=' * 70)
        print('MP4 FULL PIPELINE TEST COMPLETE')
        print('=' * 70)
        print(f'Frames processed: {frame_count}')
        print(f'Elapsed time: {elapsed:.2f}s')
        print(f'Average FPS: {(frame_count / elapsed if elapsed > 0 else 0):.2f}')
        print(f'Output: {output_path}')
        print('=' * 70)
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
