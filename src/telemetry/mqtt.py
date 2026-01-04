"""
MQTT Client for Sentinel-Edge Telemetry.
Handles asynchronous publishing of alerts to a broker.
"""
import json
import threading
import paho.mqtt.client as mqtt
import cv2
import base64
import numpy as np
from typing import Dict, Any, Optional
from core.logging import log
from core.types import DetectionResult

class SentinelMQTTClient:
    """
    Wrapper around Paho MQTT Client.
    Manages connection lifecycle and publishing of detection results.
    """

    def __init__(self, broker: str = "localhost", port: int = 1883, topic_prefix: str = "sentinel"):
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix
        self.client = mqtt.Client()
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            log.success(f"MQTT Connected to {self.broker}:{self.port}")
        else:
            log.error(f"MQTT Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        log.warning("MQTT Disconnected")

    def start(self):
        """Starts the MQTT client loop in a background thread."""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            log.error(f"Failed to connect to MQTT broker: {e}")
            # We don't raise here to avoid crashing the main system just because telemetry is down.
            # "Sovereignty" means we prioritize local function over reporting.

    def stop(self):
        """Stops the MQTT client loop."""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_frame(self, frame_image: np.ndarray):
        """
        Compresses and publishes a video frame to the stream topic.
        Resizes to standard definition to save bandwidth.
        """
        if not self.connected:
            return

        try:
            # Resize for dashboard (640px width is plenty for preview)
            # Aspect ratio usually 4:3 or 16:9
            h, w = frame_image.shape[:2]
            scale = 640 / w
            dim = (640, int(h * scale))
            resized = cv2.resize(frame_image, dim, interpolation=cv2.INTER_AREA)

            # Encode as JPEG
            success, buffer = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if not success:
                return
            
            # Publish raw bytes
            topic = f"{self.topic_prefix}/stream"
            self.client.publish(topic, buffer.tobytes())
            
        except Exception as e:
            # Don't spam logs with frame errors, just debug
            pass

    def publish_alert(self, result: DetectionResult):
        """
        Publishes an anomaly detection result to the broker.
        Only publishes if anomalies are present.
        """
        if not self.connected:
            return

        if not result.anomalies:
            return

        topic = f"{self.topic_prefix}/alerts"
        payload = result.model_dump_json() # Pydantic v2 convenience
        
        try:
            info = self.client.publish(topic, payload)
            if info.rc != mqtt.MQTT_ERR_SUCCESS:
                log.warning("Failed to publish alert to MQTT")
        except Exception as e:
            log.error(f"Error publishing alert: {e}")
