from src.core.temporal_state import TemporalStateManager
from src.core.event_manager import EventManager
from src.core.risk_state import PersistentRiskState
from src.core.system_health import SystemHealth
from src.core.performance import PerformanceMonitor
from src.core.serialization import serialize
from src.core.contracts import RiskResult

def test_temporal_confirmation():
    manager = TemporalStateManager(confirm_hits=3, clear_misses=2)
    manager.update('person', True, 0.8)
    assert not manager.is_confirmed('person')
    manager.update('person', True, 0.8)
    assert not manager.is_confirmed('person')
    manager.update('person', True, 0.8)
    assert manager.is_confirmed('person')
    manager.update('person', False)
    assert manager.is_confirmed('person')
    manager.update('person', False)
    assert not manager.is_confirmed('person')

def test_event_deduplication():
    events = EventManager(cooldown_seconds=100)
    assert events.should_emit('person_detected', 'person_1')
    assert not events.should_emit('person_detected', 'person_1')

def test_risk_persistence():
    risk = PersistentRiskState(promote_hits=2, demote_hits=2)
    risk.update('HIGH', 80)
    assert risk.state.level == 'LOW'
    risk.update('HIGH', 80)
    assert risk.state.level == 'HIGH'

def test_serialization():
    result = RiskResult(level='HIGH', score=75, reasons=['person near obstruction'])
    output = serialize(result)
    assert isinstance(output, dict)
    assert output['level'] == 'HIGH'

def test_health():
    health = SystemHealth()
    health.mark_frame()
    health.mark_inference(50)
    health.mark_communication()
    snapshot = health.snapshot()
    assert 'overall_ok' in snapshot

def test_performance():
    monitor = PerformanceMonitor()
    monitor.record_inference(40)
    monitor.record_inference(60)
    assert monitor.average_inference_ms == 50
