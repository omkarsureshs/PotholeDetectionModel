from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import json
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import base64

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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
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
    """Main detection endpoint supporting file uploads with location data"""
    try:
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
                    except json.JSONDecodeError:
                        print("Warning: Invalid location JSON format")
                
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except ValueError:
                        timestamp = datetime.now()
                
                # Generate unique filename and save
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4()}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
        
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
                except ValueError as e:
                    return jsonify({'error': str(e)}), 400
            
            elif data and 'image_base64' in data:
                # Handle base64 image
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
            return jsonify({
                'error': 'No image provided. Use file upload or JSON with image_url/image_base64.'
            }), 400
        
        # Process detection if we have a valid file
        if filepath and os.path.exists(filepath):
            try:
                # Run detection - MAKE SURE THIS RETURNS ANNOTATED IMAGE
                result = detector.detect(filepath)
                
                # Enhance detections with severity and location data
                enhanced_detections = []
                for detection in result['detections']:
                    enhanced_detection = {
                        **detection,
                        'severity': calculate_severity(detection),
                        'location': location_data,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat()
                    }
                    enhanced_detections.append(enhanced_detection)
                
                # Prepare response - ADD ANNOTATED IMAGE TO RESPONSE
                response_data = {
                    'success': True,
                    'detections': enhanced_detections,
                    'image_size': result['image_size'],
                    'processing_time': result['processing_time'],
                    'model_used': result['model_used'],
                    'total_detections': result['total_detections'],
                    'location': location_data,
                    'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat()
                }
                
                # ADD THIS: Include annotated image in response if available
                if 'annotated_image' in result:
                    response_data['annotated_image'] = result['annotated_image']
                
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return jsonify(response_data)
                
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

@app.route('/api/generate-report', methods=['POST'])
def generate_pdf_report():
    """Generate PDF report from detection data"""
    try:
        print("📄 PDF generation endpoint called")
        
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
            
        data = request.get_json()
        print(f"📊 Received data keys: {list(data.keys())}")
        
        if not data or 'detection_data' not in data:
            return jsonify({'error': 'Detection data required'}), 400
        
        detection_data = data['detection_data']
        annotated_image_data = data.get('annotated_image')
        
        print(f"🔍 Processing {len(detection_data.get('detections', []))} detections")
        print(f"🖼️ Annotated image provided: {annotated_image_data is not None}")
        
        # Try to import and use PDF generator
        try:
            print("🔄 Attempting to import PDF generator...")
            from services.pdf_generator import PDFReportGenerator
            print("✅ PDF generator imported successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return jsonify({'error': f'PDF generator import failed: {str(e)}'}), 501
        
        try:
            print("🔄 Creating PDF generator instance...")
            pdf_generator = PDFReportGenerator()
            print("✅ PDF generator instance created")
            
            print("🔄 Generating PDF report...")
            pdf_path = pdf_generator.generate_report(detection_data, annotated_image_data)
            print(f"✅ PDF generated at: {pdf_path}")
            
            # Read PDF and convert to base64
            print("🔄 Reading PDF file...")
            with open(pdf_path, 'rb') as f:
                pdf_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Clean up PDF file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print("✅ Temporary PDF file cleaned up")
            
            print("✅ PDF generation completed successfully")
            return jsonify({
                'success': True,
                'pdf_data': f"data:application/pdf;base64,{pdf_data}",
                'filename': f"pothole_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            })
            
        except Exception as e:
            print(f"❌ PDF generation error: {str(e)}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500
        
    except Exception as e:
        print(f"❌ Server error in PDF endpoint: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    
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

@app.route('/')
def home():
    """API information endpoint"""
    stats = detector.get_stats()
    
    features = [
        'file_upload', 
        'url_detection', 
        'base64_support',
        'gps_tagging',
        'severity_analysis'
    ]
    
    # Check if PDF generation is available
    try:
        from services.pdf_generator import pdf_generator
        features.append('pdf_reports')
    except ImportError:
        features.append('pdf_reports (install reportlab)')
    
    return jsonify({
        'message': 'Pothole Detection API',
        'version': '1.0.0',
        'status': 'running',
        'model_loaded': stats['model_loaded'],
        'model_type': stats['detector_type'],
        'features': features,
        'endpoints': {
            'health': '/api/health (GET)',
            'detect': '/api/detect (POST)',
            'detect_url': '/api/detect/url (POST)',
            'model_info': '/api/model/info (GET)',
            'generate_report': '/api/generate-report (POST)'
        }
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('services', exist_ok=True)
    
    # Get initial stats
    stats = detector.get_stats()
    
    print("🚀 Starting Pothole Detection API...")
    print("📡 Server: http://localhost:5000")
    print("🔗 Health: http://localhost:5000/api/health")
    print("🌐 Features: File upload, Web URLs, GPS tagging, Severity analysis")
    
    # Check PDF capability
    try:
        from services.pdf_generator import pdf_generator
        print("📄 PDF Reports: ✅ Available")
    except ImportError:
        print("📄 PDF Reports: ⚠️  Install reportlab: pip install reportlab")
    
    if stats['model_loaded']:
        print("✅ YOLO model loaded successfully!")
    else:
        print("⚠️  Using mock detection")
        print("💡 To use real detection, ensure your model file exists at: model/best.pt")
    
    print("\n📋 Available Endpoints:")
    print("   GET  /                 - API information")
    print("   GET  /api/health       - Health check")
    print("   POST /api/detect       - Detect potholes (file upload)")
    print("   POST /api/detect/url   - Detect potholes (URL)")
    print("   POST /api/generate-report - Generate PDF report")
    print("   GET  /api/model/info   - Model information")
    
    app.run(debug=True, host='0.0.0.0', port=5000)