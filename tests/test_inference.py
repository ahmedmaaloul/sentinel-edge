"""
Unit tests for the Inference module.
Mocks mlx_vlm interactions.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from inference.engine import MLXInferenceEngine
from core.types import SentinelFrame
from core.exceptions import ModelLoadError

@pytest.fixture
def mock_mlx_vlm():
    with patch("inference.engine.load") as mock_load, \
         patch("inference.engine.generate") as mock_gen:
        
        # Setup load return
        mock_model = MagicMock()
        mock_processor = MagicMock()
        mock_load.return_value = (mock_model, mock_processor)
        
        # Setup generate return
        mock_gen.return_value = "No anomalies detected."
        
        yield mock_load, mock_gen

def test_engine_initialization(mock_mlx_vlm):
    """Verifies engine initializes but doesn't load until requested."""
    engine = MLXInferenceEngine()
    assert engine._is_loaded is False

def test_engine_loading(mock_mlx_vlm):
    """Verifies model loading."""
    mock_load, _ = mock_mlx_vlm
    engine = MLXInferenceEngine()
    engine.load_model()
    
    assert engine._is_loaded is True
    mock_load.assert_called_once()

def test_prediction_without_loading_raises_error():
    """Verifies error when predicting before loading."""
    engine = MLXInferenceEngine()
    frame = SentinelFrame(timestamp=0, frame_id=1, image=np.zeros((10,10,3)))
    
    with pytest.raises(ModelLoadError):
        engine.predict(frame)

def test_prediction_flow(mock_mlx_vlm):
    """Verifies the prediction data flow."""
    _, mock_gen = mock_mlx_vlm
    mock_gen.return_value = "Alert: Smoke detected in the sector."
    
    engine = MLXInferenceEngine()
    engine.load_model()
    
    # Create valid frame
    frame = SentinelFrame(
        timestamp=123.456,
        frame_id=1,
        image=np.zeros((224, 224, 3), dtype=np.uint8)
    )
    
    result = engine.predict(frame)
    
    assert result.frame_id == 1
    assert "Smoke detected" in result.raw_output
    assert len(result.anomalies) > 0
    assert result.anomalies[0].label == "HAZARD_DETECTED"
