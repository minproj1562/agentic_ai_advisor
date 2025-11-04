# app/api/v1/endpoints/messages.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.services.websocket_manager import manager
from app.models.message import Message, Conversation
from typing import List
import json

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time messaging"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message based on type
            if message_data.get("type") == "chat":
                # Save message to database
                message = Message(
                    sender_id=user_id,
                    receiver_id=message_data.get("receiver_id"),
                    content=message_data.get("content"),
                    message_type="text"
                )
                await message.save()
                
                # Send to receiver
                await manager.send_json(
                    {
                        "type": "chat",
                        "sender_id": user_id,
                        "content": message_data.get("content"),
                        "timestamp": message.created_at.isoformat()
                    },
                    message_data.get("receiver_id")
                )
            
            elif message_data.get("type") == "typing":
                # Notify receiver that sender is typing
                await manager.send_json(
                    {
                        "type": "typing",
                        "sender_id": user_id
                    },
                    message_data.get("receiver_id")
                )
            
            elif message_data.get("type") == "notification":
                # Handle notification
                await manager.send_json(
                    message_data,
                    message_data.get("receiver_id")
                )
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await manager.disconnect(websocket, user_id)

@router.get("/conversations/{user_id}")
async def get_conversations(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Get user's conversations"""
    try:
        if current_user.uid != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        conversations = await Conversation.find(
            {"$or": [
                {"participant1_id": user_id},
                {"participant2_id": user_id}
            ]}
        ).sort(-Conversation.last_message_at).to_list()
        
        return [c.dict() for c in conversations]
    
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))