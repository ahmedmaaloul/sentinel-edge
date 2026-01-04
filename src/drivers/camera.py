"""
Camera driver for Sentinel-Edge.
Handles video capture with industrial robustness (automatic reconnection).
"""
import time
import cv2
import numpy as np
from typing import Generator, Optional, Tuple
from core.types import SentinelFrame
from core.exceptions import StreamCaptureError
from core.logging import log

class CameraDriver:
    """
    Robust camera driver for local video capture.
    Features:
    - Automatic reconnection on stream failure ("Deadman switch").
    - Strict typing.
    - Yields SentinelFrame objects.
    """

    def __init__(self, camera_index: int = 0, source_id: str = "camera_main"):
        self.camera_index = camera_index
        self.source_id = source_id
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_count = 0
        self._is_running = False

    def _connect(self) -> None:
        """Attempts to connect to the camera device."""
        log.info(f"Attempting to connect to camera {self.camera_index}...")
        try:
            self._cap = cv2.VideoCapture(self.camera_index)
            if not self._cap.isOpened():
                raise StreamCaptureError(f"Failed to open camera index {self.camera_index}")
            
            # Set generic properties for consistent behavior
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Minimize latency
            
            log.info(f"Camera {self.camera_index} connected successfully.")
        except Exception as e:
            log.error(f"Connection failed: {e}")
            self._cap = None
            raise StreamCaptureError(f"Could not connect to camera: {e}")

    def _disconnect(self) -> None:
        """Safely releases the camera resource."""
        if self._cap:
            log.info(f"Releasing camera {self.camera_index}...")
            self._cap.release()
            self._cap = None

    def capture_stream(self) -> Generator[SentinelFrame, None, None]:
        """
        Yields frames from the camera indefinitely.
        Handles reconnection automatically upon failure.
        """
        self._is_running = True
        
        while self._is_running:
            if self._cap is None or not self._cap.isOpened():
                try:
                    self._connect()
                except StreamCaptureError:
                    log.warning("Camera unavailable, retrying in 2 seconds...")
                    time.sleep(2)
                    continue

            ret, frame = self._cap.read()

            if not ret or frame is None or frame.size == 0:
                log.warning("Empty frame received. Triggering reconnection...")
                self._disconnect()
                time.sleep(0.5)
                continue

            self._frame_count += 1
            timestamp = time.time()
            
            # Create standardized frame object
            sentinel_frame = SentinelFrame(
                timestamp=timestamp,
                frame_id=self._frame_count,
                image=frame,
                source_id=self.source_id,
                metadata={"resolution": frame.shape[:2]}
            )

            yield sentinel_frame

    def stop(self):
        """Stops the capture loop."""
        self._is_running = False
        self._disconnect()
