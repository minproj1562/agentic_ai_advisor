# app/services/websocket_manager.py
from typing import Dict, Set
from fastapi import WebSocket
import json

class WebSocketManager:
    def __init__(self):
        # user_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # conversation_id -> Set of user_ids currently typing
        self.typing_users: Dict[str, Set[str]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Connect a new WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Clean up typing status
        for conv_id in list(self.typing_users.keys()):
            if user_id in self.typing_users[conv_id]:
                self.typing_users[conv_id].remove(user_id)
                if not self.typing_users[conv_id]:
                    del self.typing_users[conv_id]
    
    async def send_message(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast_typing(self, user_id: str, conversation_id: str, is_typing: bool):
        """Broadcast typing status"""
        if is_typing:
            if conversation_id not in self.typing_users:
                self.typing_users[conversation_id] = set()
            self.typing_users[conversation_id].add(user_id)
        else:
            if conversation_id in self.typing_users:
                self.typing_users[conversation_id].discard(user_id)
        
        # Notify other participants
        # This is simplified - in production, get actual participants from DB
        for uid, ws in self.active_connections.items():
            if uid != user_id:
                await ws.send_json({
                    "type": "typing_status",
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "is_typing": is_typing
                })
    
    async def is_typing(self, user_id: str, conversation_id: str) -> bool:
        """Check if user is typing in conversation"""
        return conversation_id in self.typing_users and user_id in self.typing_users[conversation_id]
    
    async def send_read_receipt(self, receiver_id: str, conversation_id: str):
        """Send read receipt"""
        await self.send_message(receiver_id, {
            "type": "read_receipt",
            "conversation_id": conversation_id
        })