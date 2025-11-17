import requests
import json

BASE_URL = "http://localhost:5000"

def test_api():
    print("🧪 Testing Pothole Detection API...")
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{BASE_URL}/api/health")
        print(f"✅ Health Check: {health_response.status_code}")
        print(f"📊 Response: {json.dumps(health_response.json(), indent=2)}")
    except:
        print("❌ Backend not running!")
        return
    
    # Test model info
    model_response = requests.get(f"{BASE_URL}/api/model/info")
    print(f"✅ Model Info: {model_response.status_code}")
    print(f"📋 Response: {json.dumps(model_response.json(), indent=2)}")
    
    # Test home endpoint
    home_response = requests.get(BASE_URL)
    print(f"✅ API Info: {home_response.status_code}")
    print(f"🏠 Response: {json.dumps(home_response.json(), indent=2)}")

if __name__ == "__main__":
    test_api()