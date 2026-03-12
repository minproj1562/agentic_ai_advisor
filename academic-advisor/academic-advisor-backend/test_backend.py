# test_backend.py
# Save this in your backend folder and run: python test_backend.py

import requests

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, method="GET", data=None):
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=5)
        
        print(f"\n{'='*50}")
        print(f"📍 {name}")
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS")
            try:
                print(f"   Response: {response.json()}")
            except:
                print(f"   Response: {response.text[:200]}")
        else:
            print(f"   ❌ FAILED")
            print(f"   Response: {response.text[:300]}")
    except requests.exceptions.ConnectionError:
        print(f"\n{'='*50}")
        print(f"📍 {name}")
        print(f"   ❌ CONNECTION REFUSED - Server not running!")
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"📍 {name}")
        print(f"   ❌ ERROR: {e}")

print("🔍 Testing Academic Advisor Backend...")

# Test endpoints
test_endpoint("Health Check", f"{BASE_URL}/health")
test_endpoint("API Docs", f"{BASE_URL}/docs")
test_endpoint("Chatbot Health", f"{BASE_URL}/api/v1/chatbot/health")
test_endpoint("Chatbot Suggestions", f"{BASE_URL}/api/v1/chatbot/suggestions")
test_endpoint("Chatbot Chat", f"{BASE_URL}/api/v1/chatbot/chat", "POST", {"message": "hello"})

print("\n" + "="*50)
print("🏁 Testing Complete!")