"""
Unit tests for the drivers module.
Mocks OpenCV to avoid hardware dependency.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from drivers.camera import CameraDriver
from core.types import SentinelFrame
from core.exceptions import StreamCaptureError

@pytest.fixture
def mock_cv2():
    with patch("drivers.camera.cv2") as mock_cv:
        yield mock_cv

def test_camera_connection_success(mock_cv2):
    """Verifies successful connection."""
    # Setup mock
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cv2.VideoCapture.return_value = mock_cap
    
    driver = CameraDriver(camera_index=0)
    driver._connect()
    
    mock_cv2.VideoCapture.assert_called_with(0)
    assert driver._cap is not None

def test_camera_connection_failure(mock_cv2):
    """Verifies failure handling."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_cv2.VideoCapture.return_value = mock_cap
    
    driver = CameraDriver(camera_index=99)
    with pytest.raises(StreamCaptureError):
        driver._connect()

def test_capture_stream_yields_frames(mock_cv2):
    """Verifies that the stream generator yields valid SentinelFrames."""
    # Setup mock to return one good frame then stop
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_cap.read.side_effect = [
        (True, fake_frame), # 1st frame
        (True, fake_frame), # 2nd frame
        Exception("Stop Loop") # Force stop for test
    ]
    
    mock_cv2.VideoCapture.return_value = mock_cap
    
    driver = CameraDriver()
    
    # We purposefully break the loop with an exception to test the generator
    # In a real app, we'd call stop() from another thread or similar.
    # Here we just iterate manually.
    
    gen = driver.capture_stream()
    
    frame1 = next(gen)
    assert isinstance(frame1, SentinelFrame)
    assert frame1.frame_id == 1
    assert frame1.image.shape == (100, 100, 3)
    
    frame2 = next(gen)
    assert frame2.frame_id == 2
    
    driver.stop()
