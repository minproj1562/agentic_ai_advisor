#academic-advisor-backend/app/services/messaging_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.messages import Message, Conversation

class MessagingService:
    
    async def get_user_conversations(self, user_id: str) -> List[dict]:
        """Get all conversations for a user using MongoDB"""
        conversations = []
        
        # Find conversations where user is participant
        convs = await Conversation.find({
            "$or": [
                {"participant1_id": user_id},
                {"participant2_id": user_id}
            ]
        }).sort(-Conversation.last_message_at).to_list()
        
        for conv in convs:
            # Get other participant info
            other_participant_id = (
                conv.participant2_id if conv.participant1_id == user_id 
                else conv.participant1_id
            )
            
            # Count unread messages for this conversation
            unread_count = await Message.find({
                "conversation_id": str(conv.id),
                "receiver_id": user_id,
                "is_read": False
            }).count()
            
            conversations.append({
                'id': str(conv.id),
                'participantId': other_participant_id,
                'participantName': await self._get_user_display_name(other_participant_id),
                'participantRole': await self._get_user_role(other_participant_id),
                'lastMessage': conv.last_message or '',
                'lastMessageTime': conv.last_message_at.isoformat() if conv.last_message_at else conv.created_at.isoformat(),
                'unreadCount': unread_count,
                'isOnline': False  # You'd implement presence tracking
            })
        
        return conversations
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get messages for a conversation"""
        messages = await Message.find({
            "conversation_id": conversation_id
        }).sort(-Message.created_at).skip(offset).limit(limit).to_list()
        
        return [
            {
                'id': str(msg.id),
                'senderId': msg.sender_id,
                'senderName': await self._get_user_display_name(msg.sender_id),
                'content': msg.content,
                'timestamp': msg.created_at.isoformat(),
                'isRead': msg.is_read,
                'isStarred': False,
                'attachments': []
            }
            for msg in reversed(messages)  # Reverse to show oldest first
        ]
    
    async def save_message(
        self,
        sender_id: str,
        receiver_id: str,
        content: str,
        attachments: Optional[List[str]] = None
    ) -> dict:
        """Save a message"""
        # Find or create conversation
        conversation_id = await self.get_or_create_conversation(sender_id, receiver_id)
        
        # Create message
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type="text"
        )
        await message.insert()
        
        # Update conversation
        conversation = await Conversation.get(conversation_id)
        if conversation:
            conversation.last_message = content
            conversation.last_message_at = datetime.now()
            conversation.updated_at = datetime.now()
            # Increment unread count for the receiver
            conversation.unread_count = await Message.find({
                "conversation_id": conversation_id,
                "receiver_id": receiver_id,
                "is_read": False
            }).count()
            await conversation.save()
        
        return {
            'id': str(message.id),
            'conversation_id': conversation_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'timestamp': message.created_at.isoformat(),
            'is_read': False
        }
    
    async def get_or_create_conversation(
        self,
        user1_id: str,
        user2_id: str
    ) -> str:
        """Get existing conversation or create new one"""
        # Check if conversation exists
        existing = await Conversation.find_one({
            "$or": [
                {"participant1_id": user1_id, "participant2_id": user2_id},
                {"participant1_id": user2_id, "participant2_id": user1_id}
            ]
        })
        
        if existing:
            return str(existing.id)
        
        # Create new conversation
        conversation = Conversation(
            participant1_id=user1_id,
            participant2_id=user2_id,
            last_message="",
            unread_count=0
        )
        await conversation.insert()
        
        return str(conversation.id)
    
    async def mark_as_read(self, message_id: str, user_id: str):
        """Mark message as read"""
        message = await Message.get(message_id)
        if message and message.receiver_id == user_id:
            message.is_read = True
            await message.save()
            
            # Update conversation unread count
            conversation = await Conversation.get(message.conversation_id)
            if conversation:
                conversation.unread_count = await Message.find({
                    "conversation_id": message.conversation_id,
                    "receiver_id": user_id,
                    "is_read": False
                }).count()
                await conversation.save()
    
    async def delete_message(self, message_id: str, user_id: str):
        """Delete a message"""
        message = await Message.get(message_id)
        if message and (message.sender_id == user_id or message.receiver_id == user_id):
            await message.delete()
    
async def _get_user_display_name(self, user_id: str) -> str:
    """Get user display name from Faculty or StudentProfile collections"""
    try:
        from app.models.faculty import Faculty
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        if faculty:
            return faculty.name

        from app.models.student_profile import StudentProfile
        student = await StudentProfile.find_one(StudentProfile.user_id == user_id)
        if student:
            return student.name
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not resolve display name for {user_id}: {e}")

    return f"User {user_id[:8]}"

async def _get_user_role(self, user_id: str) -> str:
    """Get user role from database"""
    try:
        from app.models.faculty import Faculty
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        if faculty:
            return "faculty"
    except Exception:
        pass
    return "student"