# app/services/websocket_manager.py
from typing import Dict, List, Optional
from fastapi import WebSocket
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.connection_times: Dict[str, datetime] = {}  # Track connection duration
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.connection_times[user_id] = datetime.utcnow()
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket")
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                duration = datetime.utcnow() - self.connection_times[user_id]
                del self.active_connections[user_id]
                del self.connection_times[user_id]
                logger.info(f"User {user_id} disconnected from WebSocket (session: {duration.total_seconds():.1f}s)")
            else:
                logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")
                    disconnected_connections.append(connection)
            
            # Clean up dead connections
            for conn in disconnected_connections:
                await self._cleanup_connection(conn, user_id)
    
    async def send_json(self, data: dict, user_id: str):
        """Send JSON data to specific user"""
        if user_id in self.active_connections:
            message = json.dumps(data)
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending JSON to {user_id}: {e}")
                    disconnected_connections.append(connection)
            
            # Clean up dead connections
            for conn in disconnected_connections:
                await self._cleanup_connection(conn, user_id)
    
    async def broadcast(
        self, 
        message: str, 
        exclude: Optional[List[str]] = None, 
        message_type: Optional[str] = "message"
    ):
        """Broadcast message to all connected users with enhanced features"""
        exclude = exclude or []
        stats = {"sent": 0, "failed": 0}
        
        for user_id, connections in list(self.active_connections.items()):
            if user_id not in exclude:
                for connection in connections[:]:  # Copy to avoid modification during iteration
                    try:
                        await connection.send_text(message)
                        stats["sent"] += 1
                    except Exception as e:
                        logger.error(f"Error broadcasting to {user_id}: {e}")
                        stats["failed"] += 1
                        await self._cleanup_connection(connection, user_id)
        
        logger.info(f"Broadcast complete: {stats['sent']} sent, {stats['failed']} failed")
    
    async def broadcast_json(
        self, 
        data: dict, 
        exclude: Optional[List[str]] = None, 
        message_type: Optional[str] = "notification"
    ):
        """Enhanced broadcast for JSON data with typing"""
        exclude = exclude or []
        message = json.dumps({**data, "type": message_type, "timestamp": datetime.utcnow().isoformat()})
        await self.broadcast(message, exclude, message_type)
    
    async def send_to_role(
        self, 
        message: str, 
        role: str, 
        exclude_user_id: Optional[str] = None
    ):
        """Send message to all users with specific role"""
        exclude = [exclude_user_id] if exclude_user_id else []
        # This would need integration with user roles - placeholder for now
        await self.broadcast(message, exclude)
        logger.info(f"Message sent to role '{role}'")
    
    async def get_active_users(self) -> Dict[str, int]:
        """Get count of active connections per user"""
        return {user_id: len(connections) for user_id, connections in self.active_connections.items()}
    
    async def _cleanup_connection(self, websocket: WebSocket, user_id: str):
        """Helper to safely remove dead connections"""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass  # Already removed
            
            if not self.active_connections[user_id]:
                if user_id in self.connection_times:
                    duration = datetime.utcnow() - self.connection_times[user_id]
                    del self.connection_times[user_id]
                del self.active_connections[user_id]
                logger.debug(f"Cleaned up all connections for {user_id}")

# Global instance
manager = ConnectionManager()