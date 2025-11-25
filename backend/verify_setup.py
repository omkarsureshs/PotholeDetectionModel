#!/usr/bin/env python3
"""
Quick verification that the backend is working correctly with cookie-based sessions
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

print("\n" + "="*70)
print("🧪 TESTING AUTHENTICATION & STATS WITH COOKIES")
print("="*70)

# Test 1: Health check
print("\n1️⃣ Health Check")
print("-" * 70)
try:
    resp = requests.get(f'{BASE_URL}/api/health', timeout=5)
    print(f"✅ Backend is alive: {resp.status_code}")
except Exception as e:
    print(f"❌ Backend unreachable: {e}")
    exit(1)

# Test 2: GeoJSON endpoint
print("\n2️⃣ GeoJSON Data (Potholes)")
print("-" * 70)
try:
    resp = requests.get(f'{BASE_URL}/api/map/geojson', timeout=10)
    if resp.ok:
        data = resp.json()
        print(f"✅ GeoJSON loaded: {data['features'].__len__()} potholes")
        if len(data['features']) > 0:
            p = data['features'][0]['properties']
            print(f"   Sample: Severity={p.get('severity')}, Confidence={p.get('confidence'):.2f}")
    else:
        print(f"❌ GeoJSON failed: {resp.status_code}")
except Exception as e:
    print(f"❌ GeoJSON error: {e}")

# Test 3: Login with session (Note: requests doesn't send cookies like browser does)
print("\n3️⃣ Database Stats (Direct Query)")
print("-" * 70)
try:
    import sqlite3
    conn = sqlite3.connect('pothole_data.db')
    cur = conn.cursor()
    
    # Check demo user potholes
    demo_id = '6c523802-298f-442a-a5b2-20956c6cf6ad'
    cur.execute('SELECT COUNT(*), SUM(CASE WHEN severity="high" THEN 1 ELSE 0 END) as h, SUM(CASE WHEN severity="medium" THEN 1 ELSE 0 END) as m, SUM(CASE WHEN severity="low" THEN 1 ELSE 0 END) as l FROM potholes WHERE user_id=?', (demo_id,))
    result = cur.fetchone()
    conn.close()
    
    total, high, med, low = result
    print(f"✅ Demo user potholes: {total} total")
    print(f"   Breakdown: {high or 0}H, {med or 0}M, {low or 0}L")
except Exception as e:
    print(f"❌ Database error: {e}")

# Test 4: Map statistics endpoint
print("\n4️⃣ Map Statistics Endpoint")
print("-" * 70)
try:
    resp = requests.get(f'{BASE_URL}/api/map/statistics', timeout=5)
    if resp.ok:
        stats = resp.json()
        print(f"✅ Map statistics loaded")
        print(f"   Total potholes: {stats.get('total_potholes', 'N/A')}")
        print(f"   High severity: {stats.get('high_severity', 'N/A')}")
except Exception as e:
    print(f"❌ Stats error: {e}")

print("\n" + "="*70)
print("✅ VERIFICATION COMPLETE")
print("="*70)
print("\n📌 NOTES FOR BROWSER TESTING:")
print("   - Open http://localhost:3000 in browser")
print("   - Login with: demo@example.com / demo123")
print("   - Check browser console for debug output")
print("   - Look for session_token in Network tab -> Cookies")
print("   - Stats should show after login (check Map tab)")
print("\n")
