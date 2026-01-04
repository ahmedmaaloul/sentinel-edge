"""
Entry point for Sentinel-Edge.
"""
import argparse
import sys
import time
from pathlib import Path

# Ensure src is in path if running directly
sys.path.append(str(Path(__file__).parent))

from drivers.camera import CameraDriver
from inference.engine import MLXInferenceEngine
from core.system import SentinelSystem
from core.logging import log

def main():
    parser = argparse.ArgumentParser(description="Sentinel-Edge: Local-First Industrial Surveillance")
    parser.add_argument("--model", type=str, default="mlx-community/Qwen2.5-VL-7B-Instruct-4bit", help="Path or Repo ID of the MLX model")
    parser.add_argument("--camera", type=int, default=0, help="Camera index to capture from")
    parser.add_argument("--mqtt-broker", type=str, default="localhost", help="MQTT Broker address (default: localhost)")
    
    args = parser.parse_args()

    log.info("Initializing Sentinel-Edge...")

    # 1. Instantiate Drivers
    # In a real complex app, we might use a DI container here
    camera = CameraDriver(camera_index=args.camera)

    # 2. Instantiate Intelligence
    # This might take a moment to load / verifying hardware
    engine = MLXInferenceEngine(model_path=args.model)
    
    # 3. Instantiate Telemetry
    from telemetry.mqtt import SentinelMQTTClient
    mqtt = SentinelMQTTClient(broker=args.mqtt_broker)

    # 4. Instantiate System Orchestrator
    system = SentinelSystem(driver=camera, engine=engine, mqtt_client=mqtt)

    # 5. Run
    # Blocks until SIGINT
    log.info("Press Ctrl+C to stop.")
    system.start(blocking=True)

if __name__ == "__main__":
    main()
