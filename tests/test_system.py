"""
Unit tests for the System Orchestrator.
"""
import pytest
import time
import threading
from unittest.mock import MagicMock
from core.system import SentinelSystem
from core.types import SentinelFrame, DetectionResult

def test_system_orchestration():
    """Verifies that the system pulls from driver, pushes to engine, and logs."""
    
    # Mock Driver
    mock_driver = MagicMock()
    # Create finite iterator
    frame1 = SentinelFrame(timestamp=1, frame_id=1, image=MagicMock())
    frame2 = SentinelFrame(timestamp=2, frame_id=2, image=MagicMock())
    mock_driver.capture_stream.return_value = iter([frame1, frame2])
    
    # Mock Engine
    mock_engine = MagicMock()
    result1 = DetectionResult(frame_id=1, timestamp=1, processing_latency_ms=10, anomalies=[])
    result2 = DetectionResult(frame_id=2, timestamp=2, processing_latency_ms=10, anomalies=[])
    mock_engine.predict.side_effect = [result1, result2]
    # Set loaded state to True so system doesn't try to load
    mock_engine._is_loaded = True

    # Init System
    system = SentinelSystem(driver=mock_driver, engine=mock_engine)
    
    # Run (blocking but finite due to mock driver iterator)
    system.start(blocking=True)
    
    # Verify Interactions
    assert mock_driver.capture_stream.called
    assert mock_engine.predict.call_count == 2
    mock_engine.predict.assert_any_call(frame1)
    mock_driver.stop.assert_called()

def test_system_graceful_shutdown():
    """Verifies that stop() breaks the loop."""
    mock_driver = MagicMock()
    # Infinite generator
    def infinite_stream():
        while True:
            yield SentinelFrame(timestamp=0, frame_id=0, image=MagicMock())
            time.sleep(0.01)
            
    mock_driver.capture_stream.side_effect = infinite_stream
    
    mock_engine = MagicMock()
    mock_engine._is_loaded = True
    mock_engine.predict.return_value = DetectionResult(frame_id=0, timestamp=0, processing_latency_ms=0)
    
    system = SentinelSystem(driver=mock_driver, engine=mock_engine)
    
    # Run in separate thread
    t = threading.Thread(target=system.start, args=(True,))
    t.start()
    
    time.sleep(0.1)
    assert system._running
    
    # Stop
    system.stop()
    t.join(timeout=1.0)
    
    assert not system._running
    assert not t.is_alive()
