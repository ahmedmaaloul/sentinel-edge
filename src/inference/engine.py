"""
MLX-based Inference Engine for Sentinel-Edge.
Optimized for Apple Silicon (M1 Pro+) using Metal Performance Shaders.
"""
import time
import mlx.core as mx
from mlx_vlm import load, generate
from typing import Any, Dict, Optional
from core.interfaces import InferenceEngine
from core.types import SentinelFrame, DetectionResult, AnomalyEvent
from core.exceptions import ModelLoadError
from core.logging import log
import numpy as np
from PIL import Image

class MLXInferenceEngine(InferenceEngine):
    """
    Inference Engine using Apple's MLX framework for VLM execution.
    Target Model: Qwen-VL-Chat-Int4 or similar quantized local models.
    """

    def __init__(self, model_path: str = "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"):
        """
        Initialize the engine.
        
        Args:
            model_path: HuggingFace model repo ID or local path. 
                        Defaults to a specific quantized model known to work well on 16GB Macs.
        """
        super().__init__() # VERIFY HARDWARE
        self.model_path = model_path
        self.model = None
        self.processor = None
        self.tokenizer = None
        self._is_loaded = False

    def load_model(self, model_path: Optional[str] = None) -> None:
        """
        Loads the VLM into Unified Memory.
        """
        path = model_path or self.model_path
        log.info(f"Loading MLX model from {path}...")
        
        try:
            # mlx_vlm.load returns (model, processor)
            # For Qwen2-VL, we strictly use mlx_vlm
            self.model, self.processor = load(path, trust_remote_code=True)
            self._is_loaded = True
            log.success(f"Model {path} loaded successfully on Metal.")
        except Exception as e:
            log.error(f"Failed to load VLM: {e}")
            raise ModelLoadError(f"Could not load MLX model: {e}")

    def predict(self, data: SentinelFrame) -> DetectionResult:
        """
        Runs VLM inference on the frame to detect anomalies.
        
        Args:
            data: SentinelFrame containing the image.
            
        Returns:
            DetectionResult with structured anomalies.
        """
        if not self._is_loaded:
            raise ModelLoadError("Model not loaded. Call load_model() first.")

        start_time = time.time()
        
        # Convert numpy (opencv) BGR to PIL RGB
        if data.image is None:
            return DetectionResult(
                frame_id=data.frame_id,
                timestamp=time.time(),
                processing_latency_ms=0,
                anomalies=[],
                raw_output="Empty Frame"
            )

        # OpenCV BGR -> RGB
        rgb_image = data.image[:, :, ::-1] 
        pil_image = Image.fromarray(rgb_image)

        # Construct Prompt for Industrial Safety
        prompt = "Describe this industrial scene. Are there any safety hazards, smoke, fire, or foreign objects? Answer briefly."

        # Generate (Blocking call, runs on GPU)
        try:
            # Prepare chat format for Qwen2.5-VL
            # We must apply the chat template to format the prompt correctly
            formatted_prompt = list()
            formatted_prompt.append({
                "role": "user", 
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ]
            })
            
            # Apply template (returns string)
            full_prompt = self.processor.apply_chat_template(
                formatted_prompt, 
                add_generation_prompt=True
            )
            
            output_text = generate(
                self.model, 
                self.processor, 
                prompt=full_prompt,
                images=pil_image,
                max_tokens=100, 
                verbose=False
            )
            
            latency_ms = (time.time() - start_time) * 1000.0
            
            # Simple heuristic parsing (Real implementation would use structured generation or regex)
            anomalies = []
            if "fire" in output_text.lower() or "smoke" in output_text.lower():
                anomalies.append(AnomalyEvent(
                    label="HAZARD_DETECTED",
                    confidence=0.9,
                    description=output_text
                ))
            
            return DetectionResult(
                frame_id=data.frame_id,
                timestamp=data.timestamp,
                processing_latency_ms=latency_ms,
                anomalies=anomalies,
                raw_output=output_text,
                system_metrics={"device": "mps"}
            )

        except Exception as e:
            log.error(f"Inference failed: {e}")
            # Return empty result with error logged, don't crash
            return DetectionResult(
                frame_id=data.frame_id, 
                timestamp=time.time(),
                processing_latency_ms=0, 
                raw_output=f"Error: {str(e)}"
            )

