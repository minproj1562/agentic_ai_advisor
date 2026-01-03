# app/api/v1/messages.py
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.message import Message, Conversation
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    MessageUpdate
)
from app.services.message_service import MessageService
from app.services.notification_service import NotificationService
from app.services.websocket_manager import WebSocketManager

router = APIRouter()
message_service = MessageService()
notification_service = NotificationService()
ws_manager = WebSocketManager()

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    faculty_id: str,
    filter: str = "all",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all conversations for a faculty member
    """
    if current_user["uid"] != faculty_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    query = db.query(Conversation).filter(
        or_(
            Conversation.participant1_id == faculty_id,
            Conversation.participant2_id == faculty_id
        )
    )
    
    # Apply filters
    if filter == "unread":
        query = query.filter(Conversation.unread_count > 0)
    elif filter == "pinned":
        query = query.filter(Conversation.is_pinned == True)
    elif filter == "archived":
        query = query.filter(Conversation.is_archived == True)
    else:  # all
        query = query.filter(Conversation.is_archived == False)
    
    # Order by last message time
    query = query.order_by(desc(Conversation.last_message_time))
    
    conversations = query.offset(skip).limit(limit).all()
    
    # Enrich with participant info and format response
    enriched_conversations = []
    for conv in conversations:
        participant_id = conv.participant2_id if conv.participant1_id == faculty_id else conv.participant1_id
        participant = db.query(User).filter(User.id == participant_id).first()
        
        last_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(desc(Message.timestamp)).first()
        
        enriched_conversations.append({
            "id": conv.id,
            "participantId": participant_id,
            "participantName": participant.name,
            "participantAvatar": participant.avatar_url,
            "participantRole": participant.role,
            "lastMessage": last_message,
            "unreadCount": conv.unread_count if conv.participant1_id == faculty_id else 0,
            "isPinned": conv.is_pinned,
            "isMuted": conv.is_muted,
            "isArchived": conv.is_archived,
            "isOnline": participant.is_online,
            "lastSeen": participant.last_seen,
            "typing": await ws_manager.is_typing(participant_id, conv.id)
        })
    
    return enriched_conversations

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get messages for a conversation
    """
    # Verify user is part of conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user["uid"] not in [conversation.participant1_id, conversation.participant2_id]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).offset(skip).limit(limit).all()
    
    return messages

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send a new message
    """
    # Verify conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user["uid"] not in [conversation.participant1_id, conversation.participant2_id]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Create message
    message = Message(
        **message_data.dict(),
        conversation_id=conversation_id,
        sender_id=current_user["uid"],
        timestamp=datetime.utcnow(),
        delivered=False,
        read=False
    )
    
    db.add(message)
    
    # Update conversation
    conversation.last_message_time = datetime.utcnow()
    if conversation.participant1_id == current_user["uid"]:
        conversation.unread_count_p2 += 1
    else:
        conversation.unread_count_p1 += 1
    
    db.commit()
    db.refresh(message)
    
    # Send real-time notification via WebSocket
    receiver_id = conversation.participant2_id if conversation.participant1_id == current_user["uid"] else conversation.participant1_id
    await ws_manager.send_message(receiver_id, {
        "type": "new_message",
        "conversation_id": conversation_id,
        "message": message.dict()
    })
    
    # Send push notification in background
    background_tasks.add_task(
        notification_service.send_message_notification,
        receiver_id,
        current_user["name"],
        message.content
    )
    
    # Mark as delivered
    background_tasks.add_task(
        message_service.mark_as_delivered,
        message.id
    )
    
    return message

@router.put("/conversations/{conversation_id}/read")
async def mark_as_read(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark all messages in a conversation as read
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user["uid"] not in [conversation.participant1_id, conversation.participant2_id]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Update unread messages
    db.query(Message).filter(
        and_(
            Message.conversation_id == conversation_id,
            Message.receiver_id == current_user["uid"],
            Message.read == False
        )
    ).update({"read": True, "read_at": datetime.utcnow()})
    
    # Reset unread count
    if conversation.participant1_id == current_user["uid"]:
        conversation.unread_count_p1 = 0
    else:
        conversation.unread_count_p2 = 0
    
    db.commit()
    
    # Notify sender via WebSocket
    sender_id = conversation.participant2_id if conversation.participant1_id == current_user["uid"] else conversation.participant1_id
    await ws_manager.send_message(sender_id, {
        "type": "messages_read",
        "conversation_id": conversation_id
    })
    
    return {"message": "Marked as read"}

@router.put("/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: str,
    message_data: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Edit a message
    """
    message = db.query(Message).filter(
        and_(
            Message.id == message_id,
            Message.sender_id == current_user["uid"]
        )
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Update message
    message.content = message_data.content
    message.edited = True
    message.edited_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    
    # Notify via WebSocket
    receiver_id = message.receiver_id
    await ws_manager.send_message(receiver_id, {
        "type": "message_edited",
        "message": message.dict()
    })
    
    return message

@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a message
    """
    message = db.query(Message).filter(
        and_(
            Message.id == message_id,
            Message.sender_id == current_user["uid"]
        )
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    receiver_id = message.receiver_id
    conversation_id = message.conversation_id
    
    db.delete(message)
    db.commit()
    
    # Notify via WebSocket
    await ws_manager.send_message(receiver_id, {
        "type": "message_deleted",
        "message_id": message_id,
        "conversation_id": conversation_id
    })
    
    return None

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time messaging
    """
    await ws_manager.connect(user_id, websocket)
    
    # Update user online status
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_online = True
        db.commit()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data["type"] == "typing":
                # Broadcast typing status
                await ws_manager.broadcast_typing(
                    user_id,
                    data["conversation_id"],
                    data["is_typing"]
                )
            elif data["type"] == "read_receipt":
                # Handle read receipts
                await ws_manager.send_read_receipt(
                    data["receiver_id"],
                    data["conversation_id"]
                )
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        
        # Update user offline status
        if user:
            user.is_online = False
            user.last_seen = datetime.utcnow()
            db.commit()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload file attachment
    """
    # Validate file
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large")
    
    allowed_types = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Upload to storage (Firebase Storage, S3, etc.)
    file_url = await message_service.upload_file(file, current_user["uid"])
    
    return {
        "url": file_url,
        "name": file.filename,
        "size": file.size,
        "type": file.content_type
    }