"""
Web Dashboard Backend.
Host: 0.0.0.0:8000
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import paho.mqtt.client as mqtt
import json
from typing import List
from pathlib import Path
from core.logging import log

app = FastAPI(title="Sentinel-Edge Dashboard")

# Enable CORS for development (Vite runs on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass # Connection likely dead

manager = ConnectionManager()

# MQTT Listener for bridging to WebSocket
mqtt_client = mqtt.Client()

import base64

def on_mqtt_message(client, userdata, msg):
    try:
        topic = msg.topic
        
        if topic.endswith("/stream"):
            # It's a binary JPEG frame
            # Convert to base64 for easy transport over text-based WS
            # (In high-perf setups we'd use binary WS, but this is simpler for React)
            b64_frame = base64.b64encode(msg.payload).decode('utf-8')
            payload = json.dumps({
                "type": "frame",
                "data": b64_frame
            })
        else:
            # It's a JSON alert
            payload = json.dumps({
                "type": "alert",
                "data": json.loads(msg.payload.decode())
            })

        # Broadcast immediately to all connected websockets
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(manager.broadcast(payload))
    except Exception as e:
        # Don't log frame errors to avoid spam
        if "stream" not in msg.topic:
            log.error(f"Failed to bridge MQTT to WS: {e}")

@app.on_event("startup")
async def startup_event():
    # Connect to local broker to listen for system alerts
    try:
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.subscribe("sentinel/#") # Subscribe to all sentinel topics
        mqtt_client.loop_start()
        log.success("Dashboard backend listening to MQTT sentinel/alerts")
    except Exception as e:
        log.warning(f"Dashboard failed to connect to MQTT: {e}. Live alerts may not work.")

@app.on_event("shutdown")
def shutdown_event():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve Frontend Static Files (Production Build)
# We expect the 'ui/dist' folder to exist later
static_dir = Path(__file__).parent.parent.parent / "ui" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
