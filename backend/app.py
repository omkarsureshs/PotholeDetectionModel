from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
import os
import uuid
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from PIL import Image
import requests
from io import BytesIO
import base64
import sqlite3
import traceback

# Import the detector with error handling
try:
    from model.pothole_detector import PotholeDetector
    detector = PotholeDetector('model/best.pt')
    MODEL_LOADED = True
except Exception as e:
    print(f"⚠️  YOLO model not loaded: {e}")
    print("💡 Using mock detection mode")
    MODEL_LOADED = False
    
    # Mock detector class for fallback
    class MockDetector:
        def get_stats(self):
            return {
                'model_loaded': False,
                'detector_type': 'mock',
                'total_detections': 0,
                'model_path': 'N/A'
            }
        
        def detect(self, image_path):
            # Mock detection for testing
            return {
                'detections': [
                    {
                        'bbox': [100, 100, 150, 150],
                        'confidence': 0.85,
                        'class': 'pothole',
                        'class_name': 'pothole'
                    }
                ],
                'image_size': [640, 480],
                'processing_time': 0.1,
                'model_used': 'mock_detector',
                'total_detections': 1
            }
    
    detector = MockDetector()

# Import map_service with error handling
try:
    from services.map_service import map_service
    MAP_SERVICE_LOADED = True
except Exception as e:
    print(f"❌ Map service failed to load: {e}")
    print("💡 Creating fallback map service")
    MAP_SERVICE_LOADED = False
    
    # Fallback map service
    class FallbackMapService:
        def get_or_create_user(self, request):
            return "fallback_user_123"
        
        def save_pothole_data(self, data, user_id, request):
            return "fallback_session"
        
        def get_user_potholes(self, user_id):
            return []
        
        def get_potholes_by_area(self, ne_lat, ne_lng, sw_lat, sw_lng):
            return []
        
        def get_recent_potholes(self, limit=50):
            return []
        
        def get_heatmap_data(self):
            return []
        
        def get_statistics(self):
            return {
                'total_potholes': 0,
                'avg_severity': 0,
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0,
                'total_users': 0,
                'total_reports': 0
            }
    
    map_service = FallbackMapService()

app = Flask(__name__)

# Enhanced CORS configuration
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

# Configuration
UPLOAD_FOLDER = 'uploads'
ANNOTATED_FOLDER = 'annotated'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ANNOTATED_FOLDER'] = ANNOTATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANNOTATED_FOLDER, exist_ok=True)
os.makedirs('reports', exist_ok=True)

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    """Register new user"""
    try:
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
        
        data = request.get_json()
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        print(f"📝 Registration attempt: {email}, {username}")
        
        if not all([email, username, password]):
            return jsonify({'error': 'Email, username, and password required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if not MAP_SERVICE_LOADED:
            return jsonify({'error': 'User service temporarily unavailable'}), 503
        
        user_id, error = map_service.create_user(
            email, username, password, 
            request.remote_addr, 
            request.headers.get('User-Agent')
        )
        
        if error:
            print(f"❌ Registration failed: {error}")
            return jsonify({'error': error}), 400
        
        print(f"✅ User registered: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user_id': user_id
        })
        
    except Exception as e:
        print(f"💥 Registration exception: {str(e)}")
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    """User login"""
    try:
        print("🔐 Login endpoint called")
        
        if not request.is_json:
            print("❌ No JSON data received")
            return jsonify({'error': 'JSON data required'}), 400
            
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        print(f"📧 Login attempt for: {email}")
        
        if not all([email, password]):
            print("❌ Missing email or password")
            return jsonify({'error': 'Email and password required'}), 400
        
        if not MAP_SERVICE_LOADED:
            # Fallback login for testing
            if email in ['demo@example.com', 'test@test.com', 'admin@example.com'] and password in ['demo123', 'test123', 'admin123']:
                user_data = {
                    'user_id': 'fallback_user',
                    'username': email.split('@')[0],
                    'email': email,
                    'session_token': 'fallback_token',
                    'statistics': {
                        'total_reports': 0,
                        'reputation_points': 0
                    }
                }
                
                response = make_response(jsonify({
                    'success': True,
                    'message': 'Login successful (fallback mode)',
                    'user': user_data
                }))
                
                response.set_cookie(
                    'session_token',
                    'fallback_token',
                    max_age=30*24*60*60,
                    httponly=True,
                    secure=False,
                    samesite='Lax'
                )
                return response
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        
        user_data, error = map_service.authenticate_user(
            email, password,
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        if error:
            print(f"❌ Authentication failed: {error}")
            return jsonify({'error': error}), 401
        
        print(f"✅ Login successful for: {user_data['username']}")
        
        response = make_response(jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_data
        }))
        
        # Set session cookie
        response.set_cookie(
            'session_token',
            user_data['session_token'],
            max_age=30*24*60*60,  # 30 days
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        print(f"💥 Login exception: {str(e)}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout_user():
    """User logout"""
    try:
        session_token = request.cookies.get('session_token')
        if session_token and MAP_SERVICE_LOADED:
            map_service.logout_user(session_token)
        
        response = make_response(jsonify({
            'success': True,
            'message': 'Logout successful'
        }))
        response.set_cookie('session_token', '', expires=0)
        return response
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user profile"""
    try:
        session_token = request.cookies.get('session_token')
        print(f"🔍 Checking session: {session_token}")
        
        if not session_token:
            return jsonify({'user': None})
        
        if not MAP_SERVICE_LOADED:
            # Fallback user for testing
            return jsonify({
                'user': {
                    'user_id': 'fallback_user',
                    'username': 'demo',
                    'email': 'demo@example.com',
                    'role': 'user',
                    'statistics': {
                        'total_reports': 0,
                        'reputation_points': 0
                    }
                }
            })
        
        user = map_service.validate_session(session_token)
        if not user:
            print("❌ Invalid session")
            response = make_response(jsonify({'user': None}))
            response.set_cookie('session_token', '', expires=0)
            return response
        
        print(f"✅ Valid session for: {user['username']}")
        
        # Get full user profile
        user_profile = map_service.get_user_profile(user['user_id'])
        return jsonify({'user': user_profile})
        
    except Exception as e:
        print(f"💥 Get user exception: {str(e)}")
        return jsonify({'error': f'Failed to get user: {str(e)}'}), 500

# =============================================================================
# TEST & HEALTH ENDPOINTS
# =============================================================================

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify backend is working"""
    return jsonify({
        'message': 'Backend is running!',
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'version': '2.0.0',
        'model_loaded': MODEL_LOADED,
        'map_service_loaded': MAP_SERVICE_LOADED
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stats = detector.get_stats()
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'model_loaded': stats['model_loaded'],
        'model_type': stats['detector_type'],
        'total_detections': stats['total_detections'],
        'map_service_loaded': MAP_SERVICE_LOADED
    })

# =============================================================================
# DETECTION UTILITY FUNCTIONS
# =============================================================================

def allowed_file(filename):
    """Check if file has allowed extension"""
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_url(url):
    """Check if URL is valid and points to an image"""
    try:
        return (url.startswith(('http://', 'https://')) and 
                any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']))
    except:
        return False

def download_image_from_url(image_url):
    """Download image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise ValueError("URL does not point to an image")
        
        return BytesIO(response.content)
    except Exception as e:
        raise ValueError(f"Failed to download image from URL: {str(e)}")

def handle_base64_image(base64_string):
    """Handle base64 encoded images"""
    try:
        # Handle data URL format: data:image/png;base64,...
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        return BytesIO(image_data)
    except Exception as e:
        raise ValueError(f"Invalid base64 image: {str(e)}")

def save_image_from_stream(image_stream, filename):
    """Save image from stream to file"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    with open(filepath, 'wb') as f:
        f.write(image_stream.getvalue())
    
    return filepath

def calculate_severity(detection):
    """Calculate pothole severity based on size and confidence"""
    try:
        bbox = detection['bbox']
        confidence = detection['confidence']
        
        # Calculate area
        area = bbox[2] * bbox[3]  # width * height
        
        # Severity scoring
        size_score = min(area / 10000, 1.0)  # Normalize area (max 100x100px = 1.0)
        confidence_score = confidence
        
        # Combined score (weighted)
        severity_score = (size_score * 0.7) + (confidence_score * 0.3)
        
        # Categorize severity
        if severity_score > 0.7:
            return {
                'level': 'high', 
                'score': round(severity_score, 3), 
                'description': 'Large pothole - immediate attention needed'
            }
        elif severity_score > 0.4:
            return {
                'level': 'medium', 
                'score': round(severity_score, 3), 
                'description': 'Medium pothole - schedule repair'
            }
        else:
            return {
                'level': 'low', 
                'score': round(severity_score, 3), 
                'description': 'Small pothole - monitor condition'
            }
    except Exception as e:
        # Fallback severity calculation
        return {
            'level': 'medium', 
            'score': 0.5, 
            'description': 'Standard pothole - requires inspection'
        }

# =============================================================================
# DETECTION ENDPOINTS
# =============================================================================

@app.route('/api/detect', methods=['POST'])
def detect_potholes():
    """Main detection endpoint with user tracking"""
    try:
        print("🎯 Detection endpoint called")
        
        # Get or create user
        session_token = request.cookies.get('session_token')
        user_info = None
        
        if session_token:
            user_info = map_service.validate_session(session_token)
        
        if user_info:
            user_id = user_info['user_id']
            print(f"✅ Authenticated user: {user_id}")
        else:
            user_id = map_service.get_or_create_user(request)
            print(f"✅ Anonymous user: {user_id}")
        
        filepath = None
        location_data = None
        timestamp = None
        
        # Check for file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': 'Invalid file type. Supported: PNG, JPG, JPEG, GIF, WebP'}), 400
                
                # Get location data from form
                location_json = request.form.get('location')
                timestamp_str = request.form.get('timestamp')
                
                if location_json:
                    try:
                        location_data = json.loads(location_json)
                        print(f"✅ Location data: {location_data}")
                    except json.JSONDecodeError:
                        print("⚠️  Invalid location JSON format")
                        # Get default location
                        location_data = {'latitude': 40.7128, 'longitude': -74.0060}
                else:
                    # Use default location if not provided
                    location_data = {'latitude': 40.7128, 'longitude': -74.0060}
                
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except ValueError:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
                
                # Generate unique filename and save
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                print(f"✅ File saved: {filepath}")
        
        # Check for JSON data with URL or base64
        elif request.is_json:
            data = request.get_json()
            
            if data and 'image_url' in data:
                # Handle URL-based detection
                image_url = data['image_url']
                if not is_valid_url(image_url):
                    return jsonify({'error': 'Invalid image URL'}), 400
                
                try:
                    image_stream = download_image_from_url(image_url)
                    filename = f"{uuid.uuid4()}.jpg"
                    filepath = save_image_from_stream(image_stream, filename)
                    print(f"✅ URL image saved: {filepath}")
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            
            elif data and 'image_base64' in data:
                # Handle base64 image
                base64_data = data['image_base64']
                try:
                    image_stream = handle_base64_image(base64_data)
                    filename = f"{uuid.uuid4()}.jpg"
                    filepath = save_image_from_stream(image_stream, filename)
                    print(f"✅ Base64 image saved: {filepath}")
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            else:
                return jsonify({'error': 'No image data provided in JSON'}), 400
        
        else:
            return jsonify({
                'error': 'No image provided. Use file upload or JSON with image_url/image_base64.'
            }), 400
        
        # Process detection if we have a valid file
        if filepath and os.path.exists(filepath):
            try:
                print(f"🔄 Processing image: {filepath}")
                
                # Run detection
                result = detector.detect(filepath)
                print(f"✅ Detection completed: {result['total_detections']} potholes found")
                
                # Enhance detections with severity and location data
                enhanced_detections = []
                for detection in result['detections']:
                    enhanced_detection = {
                        'bbox': detection['bbox'],
                        'confidence': float(detection['confidence']),
                        'class': detection.get('class', 'pothole'),
                        'class_name': detection.get('class_name', 'pothole'),
                        'severity': calculate_severity(detection),
                        'location': location_data,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'user_id': user_id
                    }
                    enhanced_detections.append(enhanced_detection)
                
                # Prepare response
                response_data = {
                    'success': True,
                    'detections': enhanced_detections,
                    'image_size': result['image_size'],
                    'processing_time': result['processing_time'],
                    'model_used': result['model_used'],
                    'total_detections': result['total_detections'],
                    'location': location_data,
                    'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                    'user_id': user_id
                }
                
                # Include annotated image in response if available
                if 'annotated_image' in result:
                    response_data['annotated_image'] = result['annotated_image']
                
                # Save to database with user tracking
                try:
                    session_id = map_service.save_pothole_data(response_data, user_id, request)
                    print(f"✅ Data saved to database: {session_id}")
                    response_data['session_id'] = session_id
                except Exception as db_error:
                    print(f"⚠️  Database save failed: {db_error}")
                    print(f"🔍 Traceback: {traceback.format_exc()}")
                    # Continue even if database save fails - still return detection results
                
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print("✅ Temporary file cleaned up")
                
                # Create response with user cookie
                response = make_response(jsonify(response_data))
                response.set_cookie('user_id', user_id, max_age=365*24*60*60, secure=False, samesite='Lax')
                print("✅ Detection response sent successfully")
                return response
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                print(f"❌ Error processing image: {str(e)}")
                print(f"🔍 Traceback: {traceback.format_exc()}")
                return jsonify({'error': f'Error processing image: {str(e)}', 'success': False}), 500
        
        return jsonify({'error': 'Failed to process image', 'success': False}), 500
        
    except Exception as e:
        print(f"💥 Server error in detection: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}', 'success': False}), 500

@app.route('/api/detect/url', methods=['POST'])
def detect_from_url():
    """Direct endpoint for URL-based detection"""
    try:
        # Get or create user for URL detection too
        user_id = map_service.get_or_create_user(request)
        
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
            
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL parameter required'}), 400
        
        image_url = data['url']
        if not is_valid_url(image_url):
            return jsonify({'error': 'Invalid URL'}), 400
        
        # Download and process image
        image_stream = download_image_from_url(image_url)
        filename = f"{uuid.uuid4()}.jpg"
        filepath = save_image_from_stream(image_stream, filename)
        
        try:
            result = detector.detect(filepath)
            
            # Enhance detections with user ID
            enhanced_detections = []
            for detection in result['detections']:
                enhanced_detection = {
                    **detection,
                    'severity': calculate_severity(detection),
                    'user_id': user_id
                }
                enhanced_detections.append(enhanced_detection)
            
            response_data = {
                'success': True,
                'detections': enhanced_detections,
                'image_size': result['image_size'],
                'processing_time': result['processing_time'],
                'model_used': result['model_used'],
                'source': 'url',
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id
            }
            
            # Save to database
            map_service.save_pothole_data(response_data, user_id, request)
            
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Return with user cookie
            response = make_response(jsonify(response_data))
            response.set_cookie('user_id', user_id, max_age=365*24*60*60)
            return response
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# =============================================================================
# SIMPLIFIED OTHER ENDPOINTS
# =============================================================================

@app.route('/api/user/location', methods=['GET'])
def get_user_location():
    """Get user location from IP geolocation"""
    try:
        # Try to get user IP
        user_ip = request.remote_addr
        
        # Try to use IP geolocation service (free service)
        if user_ip and user_ip != '127.0.0.1':
            try:
                geo_response = requests.get(
                    f'https://ipapi.co/{user_ip}/json/',
                    timeout=5
                )
                if geo_response.status_code == 200:
                    geo_data = geo_response.json()
                    return jsonify({
                        'latitude': geo_data.get('latitude', 40.7128),
                        'longitude': geo_data.get('longitude', -74.0060),
                        'city': geo_data.get('city', 'Unknown'),
                        'country': geo_data.get('country_name', 'Unknown'),
                        'source': 'ip_geolocation'
                    })
            except Exception as e:
                print(f"⚠️  Geolocation API error: {str(e)}")
        
        # Default location (New York City)
        return jsonify({
            'latitude': 40.7128,
            'longitude': -74.0060,
            'city': 'New York',
            'country': 'US',
            'source': 'default'
        })
    except Exception as e:
        print(f"❌ Location endpoint error: {str(e)}")
        return jsonify({
            'latitude': 40.7128,
            'longitude': -74.0060,
            'city': 'New York',
            'country': 'US',
            'source': 'default',
            'error': str(e)
        })

@app.route('/api/user/potholes', methods=['GET'])
def get_user_potholes():
    """Get all potholes reported by the current user"""
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return jsonify({'potholes': []})
        
        potholes = map_service.get_user_potholes(user_id)
        return jsonify({'potholes': potholes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/cookies', methods=['GET', 'POST', 'OPTIONS'])
def debug_cookies():
    """Debug endpoint to check what cookies Flask receives"""
    print("\n" + "=" * 60)
    print("🔍 DEBUG COOKIES ENDPOINT")
    print("=" * 60)
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request cookies: {dict(request.cookies)}")
    print(f"REQUEST.ENVIRON: {dict(request.environ)}")
    print("=" * 60 + "\n")
    
    return jsonify({
        'method': request.method,
        'cookies_received': dict(request.cookies),
        'headers': dict(request.headers),
        'origin': request.origin,
        'remote_addr': request.remote_addr
    })

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get statistics for the current user"""
    try:
        session_token = request.cookies.get('session_token')
        print(f"🔍 Session token from cookie: {session_token[:16] if session_token else 'NONE'}...")
        print(f"🔍 All cookies: {dict(request.cookies)}")
        
        if not session_token:
            print("❌ No session token found")
            return jsonify({
                'total_reports': 0,
                'high_severity_reports': 0,
                'medium_severity_reports': 0,
                'low_severity_reports': 0,
                'reputation_points': 0,
                'user_id': 'unknown'
            })
        
        # Get user from session
        user = map_service.validate_session(session_token)
        if not user:
            print(f"❌ Invalid session: {session_token[:16]}...")
            return jsonify({
                'total_reports': 0,
                'high_severity_reports': 0,
                'medium_severity_reports': 0,
                'low_severity_reports': 0,
                'reputation_points': 0,
                'user_id': 'unknown'
            })
        
        user_id = user['user_id']
        print(f"✅ Valid session for: {user['username']}")
        
        # Query potholes for this user
        conn = sqlite3.connect(map_service.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low
            FROM potholes
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        total = result[0] or 0
        high = result[1] or 0
        medium = result[2] or 0
        low = result[3] or 0
        
        print(f"✅ User {user['username']} stats: {total} potholes ({high}H, {medium}M, {low}L)")
        
        return jsonify({
            'total_reports': total,
            'high_severity_reports': high,
            'medium_severity_reports': medium,
            'low_severity_reports': low,
            'reputation_points': 0,
            'user_id': user_id
        })
    except Exception as e:
        print(f"❌ Error getting user stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'total_reports': 0
        }), 500

@app.route('/api/map/potholes', methods=['GET'])
def get_potholes():
    """Get potholes for map display"""
    try:
        potholes = map_service.get_recent_potholes(50)
        return jsonify({'potholes': potholes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/recent-potholes', methods=['GET'])
def get_recent_potholes():
    """Get recent potholes for map display"""
    try:
        limit = int(request.args.get('limit', 50))
        potholes = map_service.get_recent_potholes(limit)
        return jsonify({'potholes': potholes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/statistics', methods=['GET'])
def get_map_statistics():
    """Get overall statistics"""
    try:
        stats = map_service.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/heatmap', methods=['GET'])
def get_heatmap():
    """Get heatmap data for all potholes"""
    try:
        heatmap_data = map_service.get_heatmap_data()
        return jsonify({
            'success': True,
            'heatmap_data': heatmap_data,
            'total_points': len(heatmap_data)
        }), 200
    except Exception as e:
        print(f"❌ Heatmap error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/map/clusters', methods=['GET'])
def get_pothole_clusters():
    """Get pothole data grouped by severity and location clusters"""
    try:
        limit = int(request.args.get('limit', 100))
        potholes = map_service.get_recent_potholes(limit)
        
        clusters = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        for pothole in potholes:
            severity = pothole.get('severity', 'medium')
            if severity in clusters:
                clusters[severity].append(pothole)
        
        return jsonify({
            'success': True,
            'clusters': clusters,
            'total_high': len(clusters['high']),
            'total_medium': len(clusters['medium']),
            'total_low': len(clusters['low']),
            'total_potholes': sum(len(v) for v in clusters.values())
        }), 200
    except Exception as e:
        print(f"❌ Clusters error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/map/bounds', methods=['GET'])
def get_potholes_in_bounds():
    """Get potholes within geographic bounds for map view"""
    try:
        ne_lat = float(request.args.get('ne_lat', 40.913))
        ne_lng = float(request.args.get('ne_lng', -74.005))
        sw_lat = float(request.args.get('sw_lat', 40.712))
        sw_lng = float(request.args.get('sw_lng', -74.009))
        
        potholes = map_service.get_potholes_by_area(ne_lat, ne_lng, sw_lat, sw_lng)
        
        for pothole in potholes:
            severity = pothole.get('severity', 'medium')
            if severity == 'high':
                pothole['marker_color'] = '#ff4444'
                pothole['marker_size'] = 'large'
            elif severity == 'medium':
                pothole['marker_color'] = '#ffaa00'
                pothole['marker_size'] = 'medium'
            else:
                pothole['marker_color'] = '#44ff44'
                pothole['marker_size'] = 'small'
        
        return jsonify({
            'success': True,
            'potholes': potholes,
            'total': len(potholes),
            'bounds': {
                'ne': {'lat': ne_lat, 'lng': ne_lng},
                'sw': {'lat': sw_lat, 'lng': sw_lng}
            }
        }), 200
    except Exception as e:
        print(f"❌ Bounds error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/map/summary', methods=['GET'])
def get_map_summary():
    """Get comprehensive map summary with all data"""
    try:
        stats = map_service.get_statistics()
        recent_potholes = map_service.get_recent_potholes(50)
        heatmap_data = map_service.get_heatmap_data()
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'recent_potholes': recent_potholes,
            'heatmap_data': heatmap_data,
            'summary': {
                'total_potholes': stats.get('total_potholes', 0),
                'high_severity': stats.get('high_severity', 0),
                'medium_severity': stats.get('medium_severity', 0),
                'low_severity': stats.get('low_severity', 0),
                'avg_severity': stats.get('avg_severity', 0),
                'total_users': stats.get('total_users', 0),
                'total_reports': stats.get('total_reports', 0)
            }
        }), 200
    except Exception as e:
        print(f"❌ Summary error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/map/geojson', methods=['GET'])
def get_geojson():
    """Get potholes as GeoJSON for map visualization"""
    try:
        limit = int(request.args.get('limit', 100))
        potholes = map_service.get_recent_potholes(limit)
        
        features = []
        for pothole in potholes:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [pothole['longitude'], pothole['latitude']]
                },
                'properties': {
                    'id': pothole.get('id'),
                    'severity': pothole.get('severity', 'medium'),
                    'confidence': pothole.get('confidence'),
                    'timestamp': pothole.get('timestamp'),
                    'user_id': pothole.get('user_id'),
                    'color': '#ff4444' if pothole.get('severity') == 'high' else '#ffaa00' if pothole.get('severity') == 'medium' else '#44ff44'
                }
            }
            features.append(feature)
        
        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        }), 200
    except Exception as e:
        print(f"❌ GeoJSON error: {str(e)}")
        return jsonify({'error': str(e), 'type': 'FeatureCollection', 'features': []}), 500


@app.route('/api/map/save-detection', methods=['POST'])
def save_detection():
    """Save a detection payload to the database (used by frontend Save button)"""
    try:
        data = request.get_json()
        if not data or 'detection_data' not in data:
            return jsonify({'error': 'detection_data required'}), 400

        detection_data = data['detection_data']

        # Resolve user: prefer authenticated session, otherwise create/get anonymous user
        session_token = request.cookies.get('session_token')
        user_info = None
        if session_token:
            user_info = map_service.validate_session(session_token)

        if user_info:
            user_id = user_info['user_id']
        else:
            user_id = map_service.get_or_create_user(request)

        session_id = map_service.save_pothole_data(detection_data, user_id, request)
        if not session_id:
            return jsonify({'error': 'Could not save detection'}), 500

        return jsonify({'success': True, 'session_id': session_id}), 200
    except Exception as e:
        print(f"❌ Save detection error: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/info', methods=['GET'])
def model_info():
    """Get information about the loaded model"""
    stats = detector.get_stats()
    return jsonify({
        'model_loaded': stats['model_loaded'],
        'model_path': stats.get('model_path', 'N/A'),
        'total_detections': stats['total_detections'],
        'detector_type': stats['detector_type']
    })

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF report from detection data"""
    try:
        from services.pdf_generator import PDFReportGenerator
        
        data = request.json
        if not data or 'detection_data' not in data:
            return jsonify({'error': 'Detection data required'}), 400
        
        detection_data = data['detection_data']
        annotated_image = data.get('annotated_image')
        
        # Generate PDF
        pdf_generator = PDFReportGenerator()
        pdf_path = pdf_generator.generate_report(
            detection_data=detection_data,
            annotated_image_data=annotated_image
        )
        
        # Read PDF file
        with open(pdf_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')
        
        filename = os.path.basename(pdf_path)
        
        return jsonify({
            'success': True,
            'message': 'PDF report generated successfully',
            'pdf_data': f'data:application/pdf;base64,{pdf_data}',
            'filename': filename
        }), 200
        
    except Exception as e:
        print(f"❌ Report generation error: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Report generation failed: {str(e)}', 'success': False}), 500

@app.route('/')
def home():
    """API information endpoint"""
    stats = detector.get_stats()
    
    return jsonify({
        'message': 'Pothole Detection API',
        'version': '2.0.0',
        'status': 'running',
        'model_loaded': stats['model_loaded'],
        'model_type': stats['detector_type'],
        'map_service_loaded': MAP_SERVICE_LOADED,
        'endpoints': {
            'health': '/api/health (GET)',
            'detect': '/api/detect (POST)',
            'detect_url': '/api/detect/url (POST)',
            'auth_register': '/api/auth/register (POST)',
            'auth_login': '/api/auth/login (POST)',
            'auth_me': '/api/auth/me (GET)',
            'auth_logout': '/api/auth/logout (POST)',
            'user_location': '/api/user/location (GET)',
            'user_stats': '/api/user/stats (GET)',
            'user_potholes': '/api/user/potholes (GET)',
            'model_info': '/api/model/info (GET)',
            'map_potholes': '/api/map/potholes (GET)',
            'map_statistics': '/api/map/statistics (GET)',
            'generate_report': '/api/generate-report (POST)'
        }
    })

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    print("🚀 Starting Pothole Detection API v2.0...")
    print("📡 Server: http://localhost:5000")
    print("🔗 Health: http://localhost:5000/api/health")
    print("🔗 Test: http://localhost:5000/api/test")
    
    if MODEL_LOADED:
        print("✅ YOLO model loaded successfully!")
    else:
        print("⚠️  Using mock detection mode")
    
    if MAP_SERVICE_LOADED:
        print("✅ Map service loaded successfully!")
    else:
        print("⚠️  Using fallback map service")
    
    print("\n📋 Available Endpoints:")
    print("   GET  /                     - API information")
    print("   GET  /api/test             - Test endpoint")
    print("   GET  /api/health           - Health check")
    print("   POST /api/auth/register    - User registration")
    print("   POST /api/auth/login       - User login")
    print("   GET  /api/auth/me          - Get current user")
    print("   POST /api/auth/logout      - User logout")
    print("   POST /api/detect           - Detect potholes (file upload)")
    print("   POST /api/detect/url       - Detect potholes (URL)")
    
    print("\n🧪 Test Credentials:")
    print("   demo@example.com / demo123")
    print("   test@test.com / test123")
    print("   admin@example.com / admin123")
    
    # Disable debug mode and auto-reload to prevent restart on file uploads
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)