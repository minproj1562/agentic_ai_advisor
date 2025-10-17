# app/main.py - Complete Backend
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
import uuid

# Import all routers
from app.api.v1 import appointments, messages, analytics, achievements, publications, settings
from app.core.firebase import initialize_firebase
from app.core.security import get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    initialize_firebase()
    yield

app = FastAPI(
    title="Academic Advisor API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(appointments.router, prefix="/api/v1", tags=["Appointments"])
app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(achievements.router, prefix="/api/v1", tags=["Achievements"])
app.include_router(publications.router, prefix="/api/v1", tags=["Publications"])
app.include_router(settings.router, prefix="/api/v1", tags=["Settings"])

# WebSocket manager for real-time messaging
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            await manager.send_personal_message(
                json.dumps(message_data),
                message_data['receiver_id']
            )
    except WebSocketDisconnect:
        manager.disconnect(user_id)