"""
Global pytest configuration and fixtures for Sentinel-Edge.
"""
import pytest
import shutil
from pathlib import Path
from core.logging import sentinel_logger

@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """
    Sets up the test environment.
    Redirects logs to a temporary test directory.
    """
    test_log_dir = Path("tests/logs")
    if test_log_dir.exists():
        shutil.rmtree(test_log_dir)
    
    # Reconfigure logger for tests
    sentinel_logger.log_dir = test_log_dir
    sentinel_logger._configure_logger()
    
    yield
    
    # Clean up after tests (optional, kept for debugging usually)
    # if test_log_dir.exists():
    #     shutil.rmtree(test_log_dir)

@pytest.fixture
def mock_inference_engine_class():
    """
    Returns a concrete implementation of the abstract InferenceEngine for testing.
    """
    from core.interfaces import InferenceEngine
    from typing import Any, Dict

    class TestEngine(InferenceEngine):
        def load_model(self, model_path: str) -> None:
            pass

        def predict(self, data: Any) -> Dict[str, Any]:
            return {"status": "ok"}

    return TestEngine
