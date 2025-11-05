"""
WebSocket endpoints for real-time communication
"""

import asyncio
import json
from typing import Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    """
    WebSocket connection manager for real-time updates
    """
    
    def __init__(self):
        # Active connections by student_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Active connections by department
        self.department_connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, metadata: Dict = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Store connection
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = metadata or {}
        self.connection_metadata[websocket]['client_id'] = client_id
        
        # Add to department connections if applicable
        if metadata and 'department' in metadata:
            dept = metadata['department']
            if dept not in self.department_connections:
                self.department_connections[dept] = set()
            self.department_connections[dept].add(websocket)
        
        logger.info(f"WebSocket connected: {client_id}")
        
        # Send welcome message
        await self.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": "Connected successfully",
                "client_id": client_id
            }),
            client_id
        )
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        # Get client info
        metadata = self.connection_metadata.get(websocket, {})
        client_id = metadata.get('client_id')
        
        # Remove from active connections
        if client_id and client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            
            # Clean up empty lists
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        
        # Remove from department connections
        if 'department' in metadata:
            dept = metadata['department']
            if dept in self.department_connections:
                self.department_connections[dept].discard(websocket)
                
                # Clean up empty sets
                if not self.department_connections[dept]:
                    del self.department_connections[dept]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    async def send_to_department(self, message: str, department: str):
        """Send message to all clients in a department"""
        if department in self.department_connections:
            disconnected = []
            
            for connection in self.department_connections[department]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn)
    
    async def broadcast(self, message: str, exclude: WebSocket = None):
        """Broadcast message to all connections"""
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)
        
        disconnected = []
        for connection in all_connections:
            if connection != exclude:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": sum(
                len(conns) for conns in self.active_connections.values()
            ),
            "unique_clients": len(self.active_connections),
            "departments": list(self.department_connections.keys()),
            "connections_by_department": {
                dept: len(conns)
                for dept, conns in self.department_connections.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/student/{student_id}")
async def student_websocket(
    websocket: WebSocket,
    student_id: str
):
    """
    WebSocket endpoint for student real-time updates
    """
    await manager.connect(websocket, f"student:{student_id}", {
        "type": "student",
        "student_id": student_id
    })
    
    try:
        # Setup Firebase listener for student updates
        def on_student_update(data):
            asyncio.create_task(
                manager.send_personal_message(
                    json.dumps({
                        "type": "student_update",
                        "data": data
                    }),
                    f"student:{student_id}"
                )
            )
        
        # Subscribe to student document changes
        listener = firebase_manager.setup_realtime_listener(
            collection="students",
            callback=on_student_update,
            filters=[{"field": "id", "operator": "==", "value": student_id}]
        )
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
            elif message.get("type") == "get_performance":
                # Fetch and send performance data
                performance = await firebase_manager.get_collection(
                    collection=f"students/{student_id}/performance"
                )
                await websocket.send_text(json.dumps({
                    "type": "performance_data",
                    "data": performance
                }))
                
            elif message.get("type") == "get_recommendations":
                # Fetch and send recommendations
                recommendations = await firebase_manager.get_collection(
                    collection=f"students/{student_id}/recommendations"
                )
                await websocket.send_text(json.dumps({
                    "type": "recommendations",
                    "data": recommendations
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if listener:
            listener.unsubscribe()
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
        if listener:
            listener.unsubscribe()


@router.websocket("/faculty/{faculty_id}")
async def faculty_websocket(
    websocket: WebSocket,
    faculty_id: str
):
    """
    WebSocket endpoint for faculty real-time updates
    """
    # Get faculty details
    faculty = await firebase_manager.get_document(
        collection="faculty",
        document_id=faculty_id
    )
    
    if not faculty:
        await websocket.close(code=1008, reason="Faculty not found")
        return
    
    department = faculty.get("department")
    
    await manager.connect(websocket, f"faculty:{faculty_id}", {
        "type": "faculty",
        "faculty_id": faculty_id,
        "department": department
    })
    
    try:
        # Setup Firebase listener for department updates
        def on_department_update(data):
            asyncio.create_task(
                manager.send_personal_message(
                    json.dumps({
                        "type": "department_update",
                        "data": data
                    }),
                    f"faculty:{faculty_id}"
                )
            )
        
        # Subscribe to department students
        listener = firebase_manager.setup_realtime_listener(
            collection="students",
            callback=on_department_update,
            filters=[{"field": "department", "operator": "==", "value": department}]
        )
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
            elif message.get("type") == "get_department_stats":
                # Fetch and send department statistics
                students = await firebase_manager.get_collection(
                    collection="students",
                    filters=[{
                        "field": "department",
                        "operator": "==",
                        "value": department
                    }]
                )
                
                stats = {
                    "total_students": len(students),
                    "average_cgpa": sum(s.get("cgpa", 0) for s in students) / len(students) if students else 0,
                    "at_risk": sum(1 for s in students if s.get("risk_level") == "high")
                }
                
                await websocket.send_text(json.dumps({
                    "type": "department_stats",
                    "data": stats
                }))
                
            elif message.get("type") == "broadcast_announcement":
                # Broadcast announcement to department
                announcement = message.get("announcement")
                await manager.send_to_department(
                    json.dumps({
                        "type": "announcement",
                        "data": announcement
                    }),
                    department
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if listener:
            listener.unsubscribe()
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
        if listener:
            listener.unsubscribe()


@router.websocket("/admin")
async def admin_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for admin real-time monitoring
    """
    await manager.connect(websocket, "admin", {
        "type": "admin"
    })
    
    try:
        # Send initial stats
        await websocket.send_text(json.dumps({
            "type": "connection_stats",
            "data": manager.get_stats()
        }))
        
        # Setup periodic stats updates
        async def send_stats():
            while True:
                await asyncio.sleep(10)  # Send stats every 10 seconds
                try:
                    await websocket.send_text(json.dumps({
                        "type": "connection_stats",
                        "data": manager.get_stats()
                    }))
                except:
                    break
        
        # Start stats task
        stats_task = asyncio.create_task(send_stats())
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
            elif message.get("type") == "broadcast":
                # Broadcast message to all users
                await manager.broadcast(
                    json.dumps({
                        "type": "admin_broadcast",
                        "data": message.get("data")
                    }),
                    exclude=websocket
                )
                
            elif message.get("type") == "get_system_health":
                # Send system health metrics
                from app.main import health_check
                health = await health_check()
                
                await websocket.send_text(json.dumps({
                    "type": "system_health",
                    "data": health
                }))
                
    except WebSocketDisconnect:
        stats_task.cancel()
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        stats_task.cancel()
        manager.disconnect(websocket)


@router.get("/connections/stats")
async def get_connection_stats():
    """
    Get WebSocket connection statistics
    """
    return manager.get_stats()