# app/api/v1/messages.py
"""
Messages API endpoints - MongoDB/Beanie version - FIXED
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.core.security import get_current_user, FirebaseUser  # FIXED: Import FirebaseUser
from app.models.messages import Message, Conversation
from app.services.messaging_service import MessagingService
from app.services.notification_service import NotificationService
from app.utils.helpers import get_logger

logger = get_logger(__name__)

router = APIRouter()
messaging_service = MessagingService()
notification_service = NotificationService()


# ============== Pydantic Schemas ==============

class MessageCreate(BaseModel):
    content: str
    message_type: str = "text"
    attachments: Optional[List[str]] = None


class MessageUpdate(BaseModel):
    content: str


class ConversationResponse(BaseModel):
    id: str
    participantId: str
    participantName: str
    participantRole: str
    lastMessage: Optional[str] = None
    lastMessageTime: Optional[str] = None
    unreadCount: int = 0
    isOnline: bool = False
    isPinned: bool = False
    isMuted: bool = False
    isArchived: bool = False


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    receiver_id: str
    content: str
    message_type: str = "text"
    is_read: bool = False
    created_at: str
    edited: bool = False
    edited_at: Optional[str] = None


# ============== Simple WebSocket Manager ==============

class ConnectionManager:
    """Simple WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.typing_status: Dict[str, Dict[str, bool]] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_typing(self, user_id: str, conversation_id: str, is_typing: bool):
        if conversation_id not in self.typing_status:
            self.typing_status[conversation_id] = {}
        self.typing_status[conversation_id][user_id] = is_typing
    
    def is_typing(self, user_id: str, conversation_id: str) -> bool:
        return self.typing_status.get(conversation_id, {}).get(user_id, False)
    
    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections


ws_manager = ConnectionManager()


# ============== REST Endpoints ==============

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    filter: str = "all",
    skip: int = 0,
    limit: int = 50,
    current_user: FirebaseUser = Depends(get_current_user)  # FIXED
):
    """Get all conversations for current user"""
    try:
        user_id = current_user.uid  # FIXED
        
        # Build query
        query = {
            "$or": [
                {"participant1_id": user_id},
                {"participant2_id": user_id}
            ]
        }
        
        # Get conversations
        conversations = await Conversation.find(query).sort(
            -Conversation.last_message_at
        ).skip(skip).limit(limit).to_list()
        
        # Enrich with participant info
        enriched = []
        for conv in conversations:
            participant_id = (
                conv.participant2_id if conv.participant1_id == user_id 
                else conv.participant1_id
            )
            
            # Count unread
            unread_count = await Message.find({
                "conversation_id": str(conv.id),
                "receiver_id": user_id,
                "is_read": False
            }).count()
            
            enriched.append(ConversationResponse(
                id=str(conv.id),
                participantId=participant_id,
                participantName=await messaging_service._get_user_display_name(participant_id),
                participantRole=await messaging_service._get_user_role(participant_id),
                lastMessage=conv.last_message,
                lastMessageTime=conv.last_message_at.isoformat() if conv.last_message_at else None,
                unreadCount=unread_count,
                isOnline=ws_manager.is_online(participant_id),
                isPinned=False,
                isMuted=False,
                isArchived=False
            ))
        
        return enriched
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: FirebaseUser = Depends(get_current_user)  # FIXED
):
    """Get messages for a conversation"""
    try:
        user_id = current_user.uid  # FIXED
        
        # Verify user is part of conversation
        conversation = await Conversation.find_one({
            "id": conversation_id,
            "$or": [
                {"participant1_id": user_id},
                {"participant2_id": user_id}
            ]
        })
        
        if not conversation:
            conversation = await Conversation.get(conversation_id)
            if not conversation or user_id not in [conversation.participant1_id, conversation.participant2_id]:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages = await Message.find({
            "conversation_id": conversation_id
        }).sort(Message.created_at).skip(skip).limit(limit).to_list()
        
        return [
            MessageResponse(
                id=str(msg.id),
                conversation_id=msg.conversation_id,
                sender_id=msg.sender_id,
                receiver_id=msg.receiver_id,
                content=msg.content,
                message_type=msg.message_type,
                is_read=msg.is_read,
                created_at=msg.created_at.isoformat(),
                edited=False,
                edited_at=None
            )
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    current_user: FirebaseUser = Depends(get_current_user)  # FIXED
):
    """Send a new message"""
    try:
        user_id = current_user.uid  # FIXED
        
        # Get conversation
        conversation = await Conversation.get(conversation_id)
        if not conversation:
            conversation = await Conversation.find_one({"id": conversation_id})
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if user_id not in [conversation.participant1_id, conversation.participant2_id]:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Determine receiver
        receiver_id = (
            conversation.participant2_id if conversation.participant1_id == user_id 
            else conversation.participant1_id
        )
        
        # Create message
        message = Message(
            conversation_id=conversation_id,
            sender_id=user_id,
            receiver_id=receiver_id,
            content=message_data.content,
            message_type=message_data.message_type,
            is_read=False
        )
        await message.insert()
        
        # Update conversation
        conversation.last_message = message_data.content[:100]
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        await conversation.save()
        
        # Send real-time notification via WebSocket
        await ws_manager.send_personal_message(receiver_id, {
            "type": "new_message",
            "conversation_id": conversation_id,
            "message": {
                "id": str(message.id),
                "sender_id": user_id,
                "content": message_data.content,
                "timestamp": message.created_at.isoformat()
            }
        })
        
        # Send push notification in background
        background_tasks.add_task(
            _send_message_notification,
            receiver_id,
            user_id,
            message_data.content
        )
        
        return MessageResponse(
            id=str(message.id),
            conversation_id=conversation_id,
            sender_id=user_id,
            receiver_id=receiver_id,
            content=message_data.content,
            message_type=message_data.message_type,
            is_read=False,
            created_at=message.created_at.isoformat(),
            edited=False,
            edited_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conversations/{conversation_id}/read")
async def mark_as_read(
    conversation_id: str,
    current_user: FirebaseUser = Depends(get_current_user)  # FIXED
):
    """Mark all messages in a conversation as read"""
    try:
        user_id = current_user.uid  # FIXED
        
        # Update all unread messages
        await Message.find({
            "conversation_id": conversation_id,
            "receiver_id": user_id,
            "is_read": False
        }).update_many({"$set": {"is_read": True}})
        
        # Notify sender via WebSocket
        conversation = await Conversation.get(conversation_id)
        if not conversation:
            conversation = await Conversation.find_one({"id": conversation_id})
        
        if conversation:
            sender_id = (
                conversation.participant2_id if conversation.participant1_id == user_id 
                else conversation.participant1_id
            )
            await ws_manager.send_personal_message(sender_id, {
                "type": "messages_read",
                "conversation_id": conversation_id
            })
        
        return {"message": "Marked as read"}
        
    except Exception as e:
        logger.error(f"Error marking as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    current_user: FirebaseUser = Depends(get_current_user)  # FIXED
):
    """Delete a message"""
    try:
        user_id = current_user.uid  # FIXED
        
        message = await Message.get(message_id)
        if not message:
            message = await Message.find_one({"id": message_id})
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message.sender_id != user_id:
            raise HTTPException(status_code=403, detail="Can only delete your own messages")
        
        receiver_id = message.receiver_id
        conversation_id = message.conversation_id
        
        await message.delete()
        
        # Notify via WebSocket
        await ws_manager.send_personal_message(receiver_id, {
            "type": "message_deleted",
            "message_id": message_id,
            "conversation_id": conversation_id
        })
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== WebSocket Endpoint ==============

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """WebSocket endpoint for real-time messaging"""
    await ws_manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "typing":
                await ws_manager.broadcast_typing(
                    user_id,
                    data.get("conversation_id", ""),
                    data.get("is_typing", False)
                )
                conversation = await Conversation.get(data.get("conversation_id"))
                if conversation:
                    other_user = (
                        conversation.participant2_id if conversation.participant1_id == user_id 
                        else conversation.participant1_id
                    )
                    await ws_manager.send_personal_message(other_user, {
                        "type": "typing",
                        "conversation_id": data.get("conversation_id"),
                        "user_id": user_id,
                        "is_typing": data.get("is_typing", False)
                    })
                    
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(user_id)


# ============== Helper Functions ==============

async def _send_message_notification(receiver_id: str, sender_id: str, content: str):
    """Background task to send notification"""
    try:
        sender_name = await messaging_service._get_user_display_name(sender_id)
        await notification_service.send_notification(
            user_id=receiver_id,
            notification_type="message",
            title=f"New message from {sender_name}",
            message=content[:100] + "..." if len(content) > 100 else content,
            data={"sender_id": sender_id},
            channels=["database", "realtime"]
        )
    except Exception as e:
        logger.error(f"Failed to send message notification: {e}")


# ============== File Upload ==============

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: FirebaseUser = Depends(get_current_user)  # FIXED
):
    """Upload file attachment"""
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    
    allowed_types = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    return {
        "url": f"/uploads/{file.filename}",
        "name": file.filename,
        "size": len(content),
        "type": file.content_type,
        "message": "File upload placeholder - implement with your storage service"
    }