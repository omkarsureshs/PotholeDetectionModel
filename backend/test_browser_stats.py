#!/usr/bin/env python3
"""
Test the stats endpoint with proper session cookie handling.
Simulates browser behavior by preserving cookies between requests.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = 'http://localhost:5000'

# Create a session that persists cookies
session = requests.Session()

# Add retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)

print("=" * 60)
print("🔐 STEP 1: Login")
print("=" * 60)

login_data = {
    "email": "demo@example.com",
    "password": "demo123"
}

resp1 = session.post(f'{BASE}/api/auth/login', json=login_data)
print(f"Status: {resp1.status_code}")
print(f"Response: {resp1.json()}")

print(f"\n📦 Cookies after login:")
token = session.cookies.get('session_token')
if token:
    print(f"  session_token: {token[:20]}...")
else:
    print(f"  session_token: NOT FOUND")

print("\n" + "=" * 60)
print("📊 STEP 2: Get User Stats (WITH COOKIES)")
print("=" * 60)

resp2 = session.get(f'{BASE}/api/user/stats')
print(f"Status: {resp2.status_code}")
stats = resp2.json()
print(f"Response:")
for key, val in stats.items():
    print(f"  {key}: {val}")

print("\n" + "=" * 60)
print("📊 VERIFICATION")
print("=" * 60)

if stats.get('user_id') == '6c523802-298f-442a-a5b2-20956c6cf6ad':
    print("✅ Session validation working! User recognized.")
    print(f"   Reports: {stats['total_reports']} (High: {stats['high_severity_reports']}, Medium: {stats['medium_severity_reports']}, Low: {stats['low_severity_reports']})")
else:
    print("❌ Session validation FAILED! User not recognized.")
    print(f"   Got user_id: {stats.get('user_id')}")

print("\n" + "=" * 60)
print("🧪 TEST COMPLETE")
print("=" * 60)
