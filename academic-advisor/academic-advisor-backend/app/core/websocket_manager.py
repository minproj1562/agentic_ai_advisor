# academic-advisor/academic-advisor-backend/app/core/websocket_manager.py
"""
WebSocket connection management
Real-time communication handler
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime
from app.core.logging import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        # Store active connections by student_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        # Message queue for offline users
        self.message_queue: Dict[str, List[Dict]] = {}
        # Heartbeat tracking
        self.last_heartbeat: Dict[WebSocket, datetime] = {}
        
    async def connect(self, websocket: WebSocket, student_id: str):
        """
        Accept and register new WebSocket connection
        """
        await websocket.accept()
        
        if student_id not in self.active_connections:
            self.active_connections[student_id] = []
        
        self.active_connections[student_id].append(websocket)
        self.connection_metadata[websocket] = {
            'student_id': student_id,
            'connected_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        self.last_heartbeat[websocket] = datetime.utcnow()
        
        logger.info(f"WebSocket connected for student: {student_id}")
        
        # Send queued messages if any
        await self._send_queued_messages(websocket, student_id)
        
        # Start heartbeat
        asyncio.create_task(self._heartbeat(websocket))
    
    def disconnect(self, student_id: str, websocket: WebSocket = None):
        """
        Remove WebSocket connection
        """
        if student_id in self.active_connections:
            if websocket:
                if websocket in self.active_connections[student_id]:
                    self.active_connections[student_id].remove(websocket)
                    
                if websocket in self.connection_metadata:
                    del self.connection_metadata[websocket]
                    
                if websocket in self.last_heartbeat:
                    del self.last_heartbeat[websocket]
            else:
                # Remove all connections for the student
                for ws in self.active_connections[student_id]:
                    if ws in self.connection_metadata:
                        del self.connection_metadata[ws]
                    if ws in self.last_heartbeat:
                        del self.last_heartbeat[ws]
                
                del self.active_connections[student_id]
        
        logger.info(f"WebSocket disconnected for student: {student_id}")
    
    async def send_personal_message(self, message: str, student_id: str):
        """
        Send message to specific student
        """
        if student_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[student_id]:
                try:
                    await connection.send_text(message)
                    self.connection_metadata[connection]['last_activity'] = datetime.utcnow()
                except WebSocketDisconnect:
                    disconnected.append(connection)
                except Exception as e:
                    logger.error(f"Error sending message to {student_id}: {str(e)}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(student_id, conn)
        else:
            # Queue message for offline user
            self._queue_message(student_id, message)
    
    async def send_json(self, data: Dict, student_id: str):
        """
        Send JSON data to specific student
        """
        message = json.dumps(data, default=str)
        await self.send_personal_message(message, student_id)
    
    async def broadcast(self, message: str, department: str = None):
        """
        Broadcast message to all or department-specific connections
        """
        for student_id, connections in self.active_connections.items():
            # Filter by department if specified
            if department:
                # Check if student belongs to department (would need additional logic)
                pass
            
            for connection in connections:
                try:
                    await connection.send_text(message)
                except:
                    pass
    
    async def send_analysis_update(
        self,
        student_id: str,
        analysis_type: str,
        data: Dict
    ):
        """
        Send analysis update to student
        """
        update = {
            'type': 'analysis_update',
            'analysis_type': analysis_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.send_json(update, student_id)
    
    async def send_progress_update(
        self,
        student_id: str,
        operation: str,
        progress: float,
        message: str = None
    ):
        """
        Send progress update for long-running operations
        """
        update = {
            'type': 'progress_update',
            'operation': operation,
            'progress': progress,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.send_json(update, student_id)
    
    def _queue_message(self, student_id: str, message: str):
        """
        Queue message for offline user
        """
        if student_id not in self.message_queue:
            self.message_queue[student_id] = []
        
        self.message_queue[student_id].append({
            'message': message,
            'queued_at': datetime.utcnow().isoformat()
        })
        
        # Limit queue size
        if len(self.message_queue[student_id]) > 100:
            self.message_queue[student_id] = self.message_queue[student_id][-100:]
    
    async def _send_queued_messages(self, websocket: WebSocket, student_id: str):
        """
        Send queued messages to newly connected user
        """
        if student_id in self.message_queue:
            for msg_data in self.message_queue[student_id]:
                try:
                    await websocket.send_text(msg_data['message'])
                except:
                    break
            
            # Clear queue after sending
            del self.message_queue[student_id]
    
    async def _heartbeat(self, websocket: WebSocket):
        """
        Send periodic heartbeat to keep connection alive
        """
        try:
            while websocket in self.connection_metadata:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
                try:
                    await websocket.send_json({'type': 'heartbeat'})
                    self.last_heartbeat[websocket] = datetime.utcnow()
                except:
                    # Connection lost
                    metadata = self.connection_metadata.get(websocket, {})
                    student_id = metadata.get('student_id')
                    if student_id:
                        self.disconnect(student_id, websocket)
                    break
        except Exception as e:
            logger.error(f"Heartbeat error: {str(e)}")
    
    async def check_connection_health(self):
        """
        Check health of all connections
        """
        current_time = datetime.utcnow()
        stale_connections = []
        
        for websocket, last_beat in self.last_heartbeat.items():
            time_diff = (current_time - last_beat).total_seconds()
            
            if time_diff > 60:  # No heartbeat for 60 seconds
                metadata = self.connection_metadata.get(websocket, {})
                student_id = metadata.get('student_id')
                
                if student_id:
                    stale_connections.append((student_id, websocket))
        
        # Disconnect stale connections
        for student_id, websocket in stale_connections:
            logger.warning(f"Disconnecting stale connection for {student_id}")
            self.disconnect(student_id, websocket)
    
    def get_connection_stats(self) -> Dict:
        """
        Get statistics about active connections
        """
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        unique_students = len(self.active_connections)
        
        return {
            'total_connections': total_connections,
            'unique_students': unique_students,
            'queued_messages': sum(len(msgs) for msgs in self.message_queue.values()),
            'active_students': list(self.active_connections.keys())
        }

# Global connection manager instance
manager = ConnectionManager()