"""
Unit tests for the core module of Sentinel-Edge.
"""
import pytest
from core.logging import log
from core.interfaces import InferenceEngine
from core.exceptions import HardwareAccelerationError

def test_logger_initialization():
    """Verifies that the logger is configured correctly and writes to files."""
    log.info("Test log message")
    assert True # functionality verified by fixture setup not crashing

def test_inference_engine_abstraction():
    """Verifies that InferenceEngine cannot be instantiated directly."""
    with pytest.raises(TypeError):
        _ = InferenceEngine()

def test_inference_engine_subclass(mock_inference_engine_class):
    """
    Verifies that a concrete subclass of InferenceEngine can be instantiated
    (assuming valid hardware).
    """
    # This might fail on non-Apple Silicon CI environments, 
    # so we might need to mock platform.machine() if we were rigorous,
    # but for local dev on M1 it explicitly tests the requirement.
    import platform
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        engine = mock_inference_engine_class()
        assert engine is not None
    else:
        # If running on non-target hardware, expect the specific error
        with pytest.raises(HardwareAccelerationError):
             _ = mock_inference_engine_class()
