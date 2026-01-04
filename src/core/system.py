"""
Core system orchestrator for Sentinel-Edge.
Manages the lifecycle of drivers and inference optimization.
"""
import time
import signal
import threading
from typing import Optional
from drivers.camera import CameraDriver
from core.interfaces import InferenceEngine
from core.logging import log
from core.types import DetectionResult
from telemetry.mqtt import SentinelMQTTClient

class SentinelSystem:
    """
    Main application controller.
    Wiring: CameraDriver -> SentinelFrame -> InferenceEngine -> DetectionResult -> Logger
    """

    def __init__(self, driver: CameraDriver, engine: InferenceEngine, mqtt_client: Optional[SentinelMQTTClient] = None):
        self.driver = driver
        self.engine = engine
        self.mqtt = mqtt_client
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, blocking: bool = True):
        """
        Starts the main processing loop.
        
        Args:
            blocking: If True, blocks the calling thread until stopped.
        """
        if self._running:
            log.warning("System already running.")
            return

        self._running = True
        self._setup_signal_handlers()
        
        log.info("Sentinel-Edge System Starting...")
        
        # Start MQTT if configured
        if self.mqtt:
            log.info("Starting Telemetry...")
            self.mqtt.start()
        
        # Load model if not already loaded (lazy loading safety)
        # In a real scenario, we might want to do this explicitly before start,
        # but self-healing is good.
        try:
            # We assume the engine might check its own state, 
            # or we rely on the caller to have warmed it up.
            # But just in case:
            if hasattr(self.engine, '_is_loaded') and not self.engine._is_loaded:
                 log.info("Warm-up: Loading model...")
                 self.engine.load_model()
        except Exception as e:
            log.critical(f"Failed to initialize engine: {e}")
            self._running = False
            return

        if blocking:
            self._run_loop()
        else:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def _run_loop(self):
        """The main infinite loop."""
        log.success("Status: ONLINE. Monitoring stream...")
        
        try:
            for frame in self.driver.capture_stream():
                if not self._running:
                    break
                
                # Inference
                result = self.engine.predict(frame)
                
                # Logging / Telemetry
                self._handle_result(result)
                
                # Publish Live Feed (Best effort)
                if self.mqtt and frame.image is not None:
                    self.mqtt.publish_frame(frame.image)
                
                # Simple throttling for thermal management if needed
                # time.sleep(0.01) 

        except Exception as e:
            log.critical(f"System crash in main loop: {e}")
        finally:
            self.stop()

    def _handle_result(self, result: DetectionResult):
        """Processes the detection result."""
        # Log latency for performance tuning
        log.debug(f"Processed Frame {result.frame_id} in {result.processing_latency_ms:.1f}ms")
        
        # Log anomalies
        for anomaly in result.anomalies:
            log.warning(f"ANOMALY DETECTED [{anomaly.label}]: {anomaly.description}")
            
        # Publish to MQTT if anomalies found
        if self.mqtt and result.anomalies:
            self.mqtt.publish_alert(result)

    def _setup_signal_handlers(self):
        """Captures SIGINT for graceful shutdown."""
        # Only set if running in main thread
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            # Not in main thread, assume caller handles signals
            pass

    def _signal_handler(self, sig, frame):
        log.info(f"Received shutdown signal: {sig}")
        self.stop()

    def stop(self):
        """Stops the system gracefully."""
        if not self._running:
            return
            
        log.info("System shutting down...")
        self._running = False
        self.driver.stop()
        
        if self.mqtt:
            self.mqtt.stop()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            
        log.success("System Stopped.")
