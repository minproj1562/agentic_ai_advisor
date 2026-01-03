#academic-advisor-backend/app/api/v1/endpoints/messages.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, get_current_faculty, get_current_student
from app.models.messages import Message, Conversation
from app.services.messaging_service import MessagingService

router = APIRouter()
messaging_service = MessagingService()

@router.get("/conversations")
async def get_conversations(
    current_user = Depends(get_current_user)  # Now properly imported
):
    """Get user's conversations"""
    try:
        conversations = await messaging_service.get_user_conversations(current_user.uid)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """Get messages for a conversation"""
    try:
        messages = await messaging_service.get_conversation_messages(
            conversation_id, limit, offset
        )
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

@router.post("/messages")
async def send_message(
    receiver_id: str,
    content: str,
    current_user = Depends(get_current_user)
):
    """Send a message"""
    try:
        if not content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty"
            )
        
        message = await messaging_service.save_message(
            sender_id=current_user.uid,
            receiver_id=receiver_id,
            content=content.strip()
        )
        return {"message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.put("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a message as read"""
    try:
        await messaging_service.mark_as_read(message_id, current_user.uid)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark message as read: {str(e)}"
        )

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a message"""
    try:
        await messaging_service.delete_message(message_id, current_user.uid)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}"
        )