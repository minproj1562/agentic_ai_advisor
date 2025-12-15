#academic-advisor-backend/app/models/messages.py
from typing import Optional, List
from beanie import Document
from pydantic import Field
from datetime import datetime
import uuid

class Message(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str  # Add this field
    sender_id: str
    receiver_id: str
    content: str
    message_type: str = "text"  # text, file, image, etc.
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "messages"
        indexes = [
            "conversation_id",
            "sender_id",
            "receiver_id",
            "created_at"
        ]

class Conversation(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant1_id: str
    participant2_id: str
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "conversations"
        indexes = [
            "participant1_id",
            "participant2_id",
            "last_message_at"
        ]