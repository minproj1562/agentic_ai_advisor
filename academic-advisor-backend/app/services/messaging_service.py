class MessagingService:
    async def get_user_conversations(self, user_id: str) -> List[dict]:
        """Get all conversations for a user"""
        # Query conversations
        conversations = []
        
        # Get conversations where user is participant
        conv_query = db.collection('conversations')\
            .where('participants', 'array_contains', user_id)\
            .order_by('last_message_time', direction='DESCENDING')\
            .stream()
        
        for conv in conv_query:
            data = conv.to_dict()
            
            # Get other participant info
            other_participant_id = [p for p in data['participants'] if p != user_id][0]
            user_doc = db.collection('users').document(other_participant_id).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            
            # Count unread messages
            unread_query = db.collection('messages')\
                .where('conversation_id', '==', conv.id)\
                .where('receiver_id', '==', user_id)\
                .where('is_read', '==', False)\
                .stream()
            
            unread_count = sum(1 for _ in unread_query)
            
            conversations.append({
                'id': conv.id,
                'participantId': other_participant_id,
                'participantName': user_data.get('name', 'Unknown'),
                'participantRole': user_data.get('role', 'student'),
                'lastMessage': data.get('last_message', ''),
                'lastMessageTime': data.get('last_message_time', datetime.now()).isoformat(),
                'unreadCount': unread_count,
                'isOnline': user_data.get('is_online', False)
            })
        
        return conversations
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get messages for a conversation"""
        messages_query = db.collection('messages')\
            .where('conversation_id', '==', conversation_id)\
            .order_by('timestamp', direction='DESCENDING')\
            .limit(limit)\
            .offset(offset)\
            .stream()
        
        messages = []
        for msg in messages_query:
            data = msg.to_dict()
            messages.append({
                'id': msg.id,
                'senderId': data.get('sender_id'),
                'senderName': data.get('sender_name', ''),
                'content': data.get('content'),
                'timestamp': data.get('timestamp', datetime.now()).isoformat(),
                'isRead': data.get('is_read', False),
                'isStarred': data.get('is_starred', False),
                'attachments': data.get('attachments', [])
            })
        
        return messages
    
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
        
        # Get sender info
        sender_doc = db.collection('users').document(sender_id).get()
        sender_name = sender_doc.to_dict().get('name', 'Unknown') if sender_doc.exists else 'Unknown'
        
        message_data = {
            'conversation_id': conversation_id,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'receiver_id': receiver_id,
            'content': content,
            'attachments': attachments or [],
            'timestamp': datetime.now(),
            'is_read': False,
            'is_starred': False
        }
        
        # Save message
        message_ref = db.collection('messages').add(message_data)
        
        # Update conversation
        db.collection('conversations').document(conversation_id).update({
            'last_message': content,
            'last_message_time': datetime.now()
        })
        
        return {'id': message_ref[1].id, **message_data}
    
    async def get_or_create_conversation(
        self,
        user1_id: str,
        user2_id: str
    ) -> str:
        """Get existing conversation or create new one"""
        # Check if conversation exists
        existing = db.collection('conversations')\
            .where('participants', 'array_contains', user1_id)\
            .stream()
        
        for conv in existing:
            if user2_id in conv.to_dict().get('participants', []):
                return conv.id
        
        # Create new conversation
        conversation_data = {
            'participants': [user1_id, user2_id],
            'created_at': datetime.now(),
            'last_message': '',
            'last_message_time': datetime.now()
        }
        
        conv_ref = db.collection('conversations').add(conversation_data)
        return conv_ref[1].id
    
    async def mark_as_read(self, message_id: str, user_id: str):
        """Mark message as read"""
        db.collection('messages').document(message_id).update({
            'is_read': True,
            'read_at': datetime.now()
        })
    
    async def delete_message(self, message_id: str, user_id: str):
        """Delete a message"""
        db.collection('messages').document(message_id).delete()