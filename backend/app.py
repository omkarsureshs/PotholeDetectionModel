from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import time
import random
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import base64
import re
from utils.image_annotator import annotator
    

# Import the detector at the top
from model.pothole_detector import PotholeDetector

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize detector
detector = PotholeDetector()

def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_url(url):
    """Check if URL is valid"""
    try:
        # Simple URL validation without external library
        return url.startswith(('http://', 'https://')) and '.' in url
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
        
        # Check if it's an image by content type or file extension
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            # Also check URL extension as fallback
            if not any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                raise ValueError("URL does not point to a supported image format")
        
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

@app.route('/api/health', methods=['GET'])
def health_check():
    stats = detector.get_stats()
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'model_loaded': stats['model_loaded'],
        'model_type': stats['detector_type'],
        'total_detections': stats['total_detections']
    })

@app.route('/api/detect', methods=['POST'])
def detect_potholes():
    try:
        image_file = None
        image_stream = None
        filepath = None
        
        # Check for file upload (multipart/form-data)
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': 'Invalid file type'}), 400
                
                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
        
        # Check for JSON data (application/json)
        elif request.is_json:
            data = request.get_json()
            
            # Check for image URL
            if data and 'image_url' in data:
                image_url = data['image_url']
                if not is_valid_url(image_url):
                    return jsonify({'error': 'Invalid URL'}), 400
                
                try:
                    image_stream = download_image_from_url(image_url)
                    filename = f"{uuid.uuid4()}.jpg"
                    filepath = save_image_from_stream(image_stream, filename)
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            
            # Check for base64 image
            elif data and 'image_base64' in data:
                base64_data = data['image_base64']
                try:
                    image_stream = handle_base64_image(base64_data)
                    filename = f"{uuid.uuid4()}.jpg"
                    filepath = save_image_from_stream(image_stream, filename)
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            else:
                return jsonify({'error': 'No image data provided in JSON'}), 400
        
        else:
            return jsonify({'error': 'No image provided. Use file upload or JSON with URL/base64.'}), 400
        
        # Process detection
        if filepath and os.path.exists(filepath):
            try:
                result = detector.detect(filepath)
                
                # Clean up
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return jsonify({
                    'success': True,
                    'detections': result['detections'],
                    'image_size': result['image_size'],
                    'processing_time': result['processing_time'],
                    'model_used': result['model_used'],
                    'total_detections': result['total_detections'],
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': f'Error processing image: {str(e)}'}), 500
        
        return jsonify({'error': 'Failed to process image'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/detect/url', methods=['POST'])
def detect_from_url():
    """Direct endpoint for URL-based detection"""
    try:
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
            
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': True,
                'detections': result['detections'],
                'image_size': result['image_size'],
                'processing_time': result['processing_time'],
                'model_used': result['model_used'],
                'source': 'url',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/')
def home():
    stats = detector.get_stats()
    return jsonify({
        'message': 'Pothole Detection API',
        'version': '1.0.0',
        'status': 'running',
        'model_loaded': stats['model_loaded'],
        'model_type': stats['detector_type'],
        'features': ['file_upload', 'url_detection', 'base64_support']
    })

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    stats = detector.get_stats()
    print("🚀 Starting Pothole Detection API...")
    print("📡 Server: http://localhost:5000")
    print("🔗 Health: http://localhost:5000/api/health")
    print("🌐 Features: File upload, Web URLs, Paste support")
    
    if stats['model_loaded']:
        print("✅ YOLO model loaded successfully!")
    else:
        print("⚠️  Using mock detection")
    
    app.run(debug=True, host='0.0.0.0', port=5000)