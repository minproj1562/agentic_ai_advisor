# scripts/test_chatbot_db.py
"""
Test chatbot with database queries
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    print("=" * 70)
    print("🧪 TESTING CHATBOT WITH DATABASE")
    print("=" * 70)
    
    # Initialize DB
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from app.config import settings
    from app.models.syllabus import Subject, SubjectUnit, Topic, Department
    from app.models.chatbot import ChatSession, ChatMessage, ChatFeedback, ChatbotAnalyticsDoc
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    await init_beanie(
        database=db,
        document_models=[
            Subject, SubjectUnit, Topic, Department,
            ChatSession, ChatMessage, ChatFeedback, ChatbotAnalyticsDoc
        ]
    )
    
    # Test queries
    test_queries = [
        "hello",
        "what is deadlock",
        "explain normalization",
        "who teaches os",
        "careers in data science",
        "what is mutex",
        "define semaphore",
        "what is tcp",
    ]
    
    print("\n📤 TESTING CHATBOT RESPONSES:")
    print("-" * 70)
    
    from app.services.chatbot.chatbot_service import ChatbotService
    service = ChatbotService()
    
    for query in test_queries:
        print(f"\n🔹 Query: \"{query}\"")
        
        response = await service.process_message(
            user_id="test_user",
            user_type="student",
            message=query,
            student_data=None
        )
        
        if isinstance(response, dict):
            intent = response.get("intent", "?")
            confidence = response.get("confidence", "?")
            resp_type = response.get("type", "?")
            content = response.get("content", {})
            
            print(f"   Intent: {intent} | Confidence: {confidence} | Type: {resp_type}")
            
            # Show relevant content
            if resp_type == "concept_explanation":
                subject = content.get("subject", "Unknown")
                topic = content.get("topic", "Unknown")
                definition = content.get("definition", "")[:100]
                source = "📚 FROM DATABASE" if "Unknown" not in subject else "📖 FROM FALLBACK"
                print(f"   {source}")
                print(f"   Subject: {subject}")
                print(f"   Topic: {topic}")
                print(f"   Definition: {definition}...")
            elif resp_type == "career_guidance":
                career = content.get("career", {})
                print(f"   Career: {career.get('title', 'Unknown')}")
            elif resp_type == "text":
                msg = content.get("message", "")[:150]
                print(f"   Response: {msg}...")
            else:
                print(f"   Content keys: {list(content.keys())}")
        else:
            print(f"   Response: {str(response)[:100]}...")
    
    # Check what was fetched from DB
    print("\n" + "=" * 70)
    print("📊 DATABASE STATISTICS:")
    print("-" * 70)
    
    topic_count = await Topic.find().count()
    subject_count = await Subject.find().count()
    
    print(f"   Topics in DB: {topic_count}")
    print(f"   Subjects in DB: {subject_count}")
    
    if topic_count > 0:
        print("\n   ✅ Chatbot CAN fetch from your MongoDB data!")
    else:
        print("\n   ⚠️ No topics in DB - chatbot using fallback definitions")
        print("   Run: python scripts/populate_syllabus_with_topics.py")
    
    print("=" * 70)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())