# test_chatbot_complete.py (place in ROOT directory, not scripts/)
"""
Complete chatbot test - place in project root
Run: python test_chatbot_complete.py
"""

import sys
import os
import asyncio

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chatbot.chatbot_service import ChatbotService


async def test_all_queries():
    """Test all query types - COMPREHENSIVE"""
    print("🤖 Starting Chatbot Test Suite...\n")
    
    chatbot = ChatbotService()
    
    test_cases = {
        "✅ Faculty Queries (Fixed with Aliases)": [
            "who teaches dbms",
            "who teaches operating system",
            "who teaches machine learning",
            "who teaches os",
        ],
        "✅ Subject Overview (New Feature)": [
            "what is operating system",
            "what is os",
            "what is the syllabus for dbms",
            "tell me about machine learning",
            "syllabus for operating systems",
        ],
        "✅ Topic/Concept Queries": [
            "what is deadlock",
            "explain mutex",
            "define normalization",
            "what is tcp",
            "explain semaphore",
        ],
        "✅ Career Queries": [
            "how to become a data scientist",
            "career in machine learning",
            "recommend electives for AI career",
        ],
        "✅ Performance Queries": [
            "show my grades",
            "what is my cgpa",
            "my weak subjects",
        ],
        "❌ Out of Scope": [
            "who won the cricket match",
            "what's the weather",
            "tell me a joke",
        ],
    }
    
    total_tests = 0
    passed_tests = 0
    
    for category, queries in test_cases.items():
        print(f"\n{'='*70}")
        print(f"📂 {category}")
        print(f"{'='*70}")
        
        for query in queries:
            total_tests += 1
            print(f"\n🔍 Query: '{query}'")
            
            try:
                response = await chatbot.process_message(
                    user_id="test123",
                    user_type="student",
                    message=query
                )
                
                intent = response.get('intent', 'UNKNOWN')
                response_type = response.get('type', 'unknown')
                confidence = response.get('confidence', 'Low')
                
                print(f"   📌 Intent: {intent}")
                print(f"   📌 Type: {response_type}")
                print(f"   📌 Confidence: {confidence}")
                
                # Get response message
                content = response.get('content', {})
                message = content.get('message', '')
                
                if message:
                    # Show first 150 characters
                    preview = message[:150].replace('\n', ' ')
                    print(f"   💬 Response: {preview}...")
                
                # Success criteria
                if confidence in ['High', 'Medium'] or intent == 'OUT_OF_SCOPE':
                    print(f"   ✅ PASSED")
                    passed_tests += 1
                else:
                    print(f"   ⚠️  LOW CONFIDENCE (needs improvement)")
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print(f"{'='*70}\n")


async def test_specific_fixes():
    """Test the specific fixes we implemented"""
    print("\n🎯 Testing Specific Fixes...\n")
    
    chatbot = ChatbotService()
    
    fixes = [
        {
            "issue": "Faculty search fails for 'DBMS'",
            "query": "who teaches dbms",
            "expected_intent": "FACULTY_QUERY",
        },
        {
            "issue": "Syllabus queries not working",
            "query": "what is the syllabus for operating systems",
            "expected_intent": "SUBJECT_OVERVIEW",
        },
        {
            "issue": "Generic subject queries fail",
            "query": "what is os",
            "expected_intent": "SUBJECT_OVERVIEW",
        },
    ]
    
    for fix in fixes:
        print(f"\n{'─'*70}")
        print(f"🔧 Fix: {fix['issue']}")
        print(f"   Query: '{fix['query']}'")
        
        response = await chatbot.process_message(
            user_id="test123",
            user_type="student",
            message=fix['query']
        )
        
        actual_intent = response.get('intent')
        expected_intent = fix['expected_intent']
        
        if actual_intent == expected_intent:
            print(f"   ✅ FIXED! Intent: {actual_intent}")
        else:
            print(f"   ⚠️  Got: {actual_intent}, Expected: {expected_intent}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         ACADEMIC ADVISOR CHATBOT - TEST SUITE                    ║
    ║         Testing Dynamic & Fixed Implementation                   ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    # scripts/test_chatbot_complete.py
"""
Chatbot test script with proper path handling
"""

import sys
import os

# Add parent directory to path (where 'app' folder is)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now imports will work
import asyncio
from app.services.chatbot.chatbot_service import ChatbotService


async def test_chatbot():
    print("🤖 Testing Academic Advisor Chatbot...\n")
    
    chatbot = ChatbotService()
    
    # Critical test cases
    test_queries = [
        ("DBMS Faculty Fix", "who teaches dbms"),
        ("OS Faculty Fix", "who teaches operating system"),
        ("Subject Overview", "what is os"),
        ("Syllabus Query", "what is the syllabus for operating systems"),
        ("Topic Definition", "what is deadlock"),
        ("Career Query", "how to become a data scientist"),
    ]
    
    for test_name, query in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 Test: {test_name}")
        print(f"   Query: '{query}'")
        
        try:
            response = await chatbot.process_message(
                user_id="test123",
                user_type="student",
                message=query
            )
            
            intent = response.get('intent', 'UNKNOWN')
            confidence = response.get('confidence', 'Low')
            
            print(f"   ✅ Intent: {intent}")
            print(f"   ✅ Confidence: {confidence}")
            
            # Show response preview
            msg = response.get('content', {}).get('message', '')
            if msg:
                preview = msg[:100].replace('\n', ' ')
                print(f"   💬 Response: {preview}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_chatbot())
    # Run tests
    asyncio.run(test_specific_fixes())
    asyncio.run(test_all_queries())