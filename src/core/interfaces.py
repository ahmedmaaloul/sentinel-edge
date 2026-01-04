"""
Abstract interfaces for the Sentinel-Edge domain.
Defines contracts for inference engines and other core components.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import platform

from core.exceptions import HardwareAccelerationError
from core.logging import log

class InferenceEngine(ABC):
    """
    Abstract base class for all inference engines.
    Enforces Apple Silicon hardware acceleration (MPS/MLX).
    """

    def __init__(self):
        self._verify_hardware_acceleration()

    def _verify_hardware_acceleration(self):
        """
        Verifies that the runtime environment supports Apple Silicon acceleration.
        Raises HardwareAccelerationError if not on an ARM64 Mac.
        """
        system = platform.system()
        machine = platform.machine()
        
        if system != "Darwin" or machine != "arm64":
            error_msg = f"Incompatible hardware: {system} {machine}. Sentinel-Edge requires Apple Silicon (Darwin arm64)."
            log.critical(error_msg)
            raise HardwareAccelerationError(error_msg)
        
        log.info(f"Hardware acceleration verification passed: {system} {machine}")

    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """
        Loads the model from the specified path.
        
        Args:
            model_path: Absolute path to the model artifacts.
            
        Raises:
            ModelLoadError: If the model cannot be loaded.
        """
        pass

    @abstractmethod
    def predict(self, data: Any) -> Dict[str, Any]:
        """
        Runs inference on the provided data.
        
        Args:
            data: Input data (image, audio, or multimodal tensor).
            
        Returns:
            Dictionary containing detection results, confidence scores, and metadata.
        """
        pass
