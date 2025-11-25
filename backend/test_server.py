#!/usr/bin/env python3
"""Minimal Flask server for testing session cookies"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

DB_PATH = 'pothole_data.db'

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple login without model loading"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Simple auth check
    if email == 'demo@example.com' and password == 'demo123':
        token = 'test_session_token_12345'
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'user_id': '6c523802-298f-442a-a5b2-20956c6cf6ad',
                'username': 'demo',
                'email': 'demo@example.com',
                'session_token': token
            }
        })
        response.set_cookie(
            'session_token',
            token,
            max_age=24*60*60,
            httponly=False,  # Change to False for debugging
            secure=False,
            samesite='Lax'
        )
        print(f"✅ Set cookie in response: session_token={token}")
        return response, 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get user stats with cookie debugging"""
    print("\n" + "=" * 60)
    print("📊 /api/user/stats endpoint called")
    print("=" * 60)
    
    session_token = request.cookies.get('session_token')
    print(f"🔍 Cookie 'session_token': {session_token}")
    print(f"🔍 All cookies: {dict(request.cookies)}")
    print(f"🔍 Request headers: {dict(request.headers)}")
    print("=" * 60 + "\n")
    
    if not session_token:
        return jsonify({
            'total_reports': 0,
            'user_id': 'unknown'
        }), 200
    
    if session_token == 'test_session_token_12345':
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low
                FROM potholes
                WHERE user_id = '6c523802-298f-442a-a5b2-20956c6cf6ad'
            ''')
            result = cursor.fetchone()
            conn.close()
            
            total = result[0] or 0
            high = result[1] or 0
            medium = result[2] or 0
            low = result[3] or 0
            
            return jsonify({
                'total_reports': total,
                'high_severity_reports': high,
                'medium_severity_reports': medium,
                'low_severity_reports': low,
                'user_id': '6c523802-298f-442a-a5b2-20956c6cf6ad'
            }), 200
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'total_reports': 0, 'user_id': 'unknown'}), 200

if __name__ == '__main__':
    print("\n🚀 Starting minimal Flask server on port 5000...")
    print("   No YOLO model loading - debugging cookies only\n")
    app.run(debug=False, host='localhost', port=5000)
