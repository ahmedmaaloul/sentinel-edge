"""
Core type definitions for Sentinel-Edge.
Defines the strict data contracts between the Perception (Drivers) and Inference layers.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field, ConfigDict

@dataclass
class SentinelFrame:
    """
    Represents a single captured frame from the sensor suite.
    Used for high-frequency internal data transfer.
    """
    timestamp: float
    frame_id: int
    image: np.ndarray
    source_id: str = "camera_0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"<SentinelFrame id={self.frame_id} ts={self.timestamp} shape={self.image.shape}>"

    @property
    def is_valid(self) -> bool:
        """Checks if the frame contains valid data."""
        return self.image is not None and self.image.size > 0

class AnomalyEvent(BaseModel):
    """
    Represents a specific detected anomaly within a frame.
    """
    label: str
    confidence: float
    description: str
    bbox: Optional[List[int]] = None  # [x, y, w, h] if applicable

    model_config = ConfigDict(arbitrary_types_allowed=True)

class DetectionResult(BaseModel):
    """
    Structured result returned by the Inference Engine.
    Designed for easy serialization to JSON for telemetry.
    """
    frame_id: int
    timestamp: float
    processing_latency_ms: float
    anomalies: List[AnomalyEvent] = Field(default_factory=list)
    raw_output: Optional[str] = None # The raw text from the SLM
    system_metrics: Dict[str, Any] = Field(default_factory=dict) # e.g., 'memory_usage_mb'

    model_config = ConfigDict(arbitrary_types_allowed=True)
