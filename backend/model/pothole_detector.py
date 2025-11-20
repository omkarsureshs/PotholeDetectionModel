import os
import cv2
import numpy as np
from PIL import Image
import torch
import json
from datetime import datetime

class PotholeDetector:
    def __init__(self, model_path=None):
        self.model = None
        self.model_loaded = False
        self.detector_type = "none"
        self.model_path = model_path
        self.available_models = self._discover_models()
        self.total_detections = 0
        
        # Try to load the specified model or default
        if model_path:
            self.load_model(model_path)
        elif self.available_models:
            self.load_model(self.available_models[0]['path'])
    
    def _discover_models(self):
        """Discover available YOLO models in the model directory"""
        models_dir = 'model'
        available_models = []
        
        # Look for common YOLO model file patterns
        model_extensions = ['.pt', '.pth', '.onnx']
        
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if any(file.endswith(ext) for ext in model_extensions):
                    model_info = {
                        'name': file,
                        'path': os.path.join(models_dir, file),
                        'size': os.path.getsize(os.path.join(models_dir, file)),
                        'modified': datetime.fromtimestamp(
                            os.path.getmtime(os.path.join(models_dir, file))
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    available_models.append(model_info)
        
        return available_models
    
    def load_model(self, model_path):
        """Load a specific model"""
        try:
            # For real YOLO models
            if model_path.endswith('.pt') or model_path.endswith('.pth'):
                try:
                    from ultralytics import YOLO
                    self.model = YOLO(model_path)
                    self.detector_type = f"yolo_{os.path.basename(model_path)}"
                    self.model_loaded = True
                    print(f"✅ Loaded YOLO model: {model_path}")
                    return True
                except ImportError:
                    print("❌ Ultralytics YOLO not available")
                    return False
                except Exception as e:
                    print(f"❌ Error loading YOLO model: {e}")
                    return False
            
            elif model_path.endswith('.onnx'):
                # For ONNX models
                try:
                    import onnxruntime as ort
                    self.model = ort.InferenceSession(model_path)
                    self.detector_type = f"onnx_{os.path.basename(model_path)}"
                    self.model_loaded = True
                    print(f"✅ Loaded ONNX model: {model_path}")
                    return True
                except ImportError:
                    print("❌ ONNX Runtime not available")
                    return False
                except Exception as e:
                    print(f"❌ Error loading ONNX model: {e}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Error loading model {model_path}: {e}")
            self.model_loaded = False
            return False
    
    def detect(self, image_path):
        """Perform detection with the currently loaded model - NO MOCK DETECTIONS"""
        if not self.model_loaded:
            return {
                'detections': [],
                'image_size': {'width': 0, 'height': 0},
                'processing_time': 0,
                'model_used': 'no_model_loaded',
                'total_detections': 0,
                'error': 'No model loaded'
            }
        
        try:
            if self.detector_type.startswith('yolo'):
                return self._detect_yolo(image_path)
            elif self.detector_type.startswith('onnx'):
                return self._detect_onnx(image_path)
            else:
                return {
                    'detections': [],
                    'image_size': {'width': 0, 'height': 0},
                    'processing_time': 0,
                    'model_used': 'unknown_model',
                    'total_detections': 0,
                    'error': 'Unknown model type'
                }
                
        except Exception as e:
            print(f"❌ Detection error with {self.detector_type}: {e}")
            return {
                'detections': [],
                'image_size': {'width': 0, 'height': 0},
                'processing_time': 0,
                'model_used': self.detector_type,
                'total_detections': 0,
                'error': str(e)
            }
    
    def _detect_yolo(self, image_path):
        """YOLO model detection - REAL DETECTIONS ONLY"""
        import time
        start_time = time.time()
        
        results = self.model(image_path)
        processing_time = time.time() - start_time
        
        detections = []
        for result in results:
            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence > 0.25:  # Confidence threshold
                    bbox = box.xywh[0].tolist()
                    detection = {
                        'bbox': bbox,  # [x_center, y_center, width, height]
                        'confidence': confidence,
                        'class': 'pothole',
                        'class_id': int(box.cls[0])
                    }
                    detections.append(detection)
        
        self.total_detections += len(detections)
        
        # Get image dimensions
        image = Image.open(image_path)
        width, height = image.size
        
        return {
            'detections': detections,
            'image_size': {'width': width, 'height': height},
            'processing_time': round(processing_time, 3),
            'model_used': self.detector_type,
            'total_detections': len(detections)
        }
    
    def _detect_onnx(self, image_path):
        """ONNX model detection - REAL DETECTIONS ONLY"""
        # This would contain your actual ONNX inference logic
        # For now, return empty if no ONNX implementation
        return {
            'detections': [],
            'image_size': {'width': 0, 'height': 0},
            'processing_time': 0,
            'model_used': self.detector_type,
            'total_detections': 0,
            'error': 'ONNX detection not implemented'
        }
    
    def get_stats(self):
        """Get detector statistics"""
        return {
            'model_loaded': self.model_loaded,
            'detector_type': self.detector_type,
            'model_path': self.model_path,
            'total_detections': self.total_detections,
            'available_models': self.available_models
        }
    
    def switch_model(self, model_path):
        """Switch to a different model"""
        print(f"🔄 Switching to model: {model_path}")
        success = self.load_model(model_path)
        if success:
            print(f"✅ Successfully switched to: {model_path}")
        else:
            print(f"❌ Failed to switch to: {model_path}")
        return success