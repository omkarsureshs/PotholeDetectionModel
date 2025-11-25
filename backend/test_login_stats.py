import requests
import json

BASE = 'http://localhost:5000'

# Create a session to maintain cookies
session = requests.Session()

# Test login
print("🔐 Testing login...")
resp = session.post(f'{BASE}/api/auth/login', json={
    'email': 'demo@example.com',
    'password': 'demo123'
})

print(f"Login status: {resp.status_code}")
data = resp.json()
print(f"Login response: {json.dumps(data, indent=2)}")

# Test user stats with the SAME session (cookies preserved)
print("\n📊 Testing user stats...")
resp2 = session.get(f'{BASE}/api/user/stats')
print(f"Stats status: {resp2.status_code}")
stats = resp2.json()
print(f"Stats: {json.dumps(stats, indent=2)}")

print("\n✅ Test complete!")
