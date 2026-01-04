"""
Core exception definitions for Sentinel-Edge.
Ensures a unified error handling strategy across the application.
"""

class SentinelException(Exception):
    """Base exception for all Sentinel-Edge errors."""
    pass

class HardwareAccelerationError(SentinelException):
    """Raised when required hardware acceleration (MPS/MLX) is unavailable or fails."""
    pass

class ModelLoadError(SentinelException):
    """Raised when a model fails to load or initialize."""
    pass

class StreamCaptureError(SentinelException):
    """Raised when input stream (video/audio) capture fails."""
    pass
