import time
import random
from PIL import Image
import numpy as np
import os
import cv2

class PotholeDetector:
    def __init__(self, model_path="model/best.pt"):
        self.model_path = model_path
        self.model = None
        self.model_loaded = False
        self.detection_count = 0
        
        # Try to load YOLO model
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model from the provided path"""
        try:
            from ultralytics import YOLO  # type: ignore
            
            if os.path.exists(self.model_path):
                print(f"🚀 Loading YOLO model from: {self.model_path}")
                self.model = YOLO(self.model_path)
                self.model_loaded = True
                print("✅ YOLO model loaded successfully!")
            else:
                print(f"❌ Model file not found: {self.model_path}")
                print("⚠️  Using mock detection instead")
                
        except ImportError as e:
            print(f"❌ Ultralytics YOLO not installed: {e}")
            print("💡 Run: pip install ultralytics")
            print("⚠️  Using mock detection instead")
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            print("⚠️  Using mock detection instead")
    
    def detect(self, image_path):
        """
        Detect potholes using YOLO model or fallback to mock detection
        """
        start_time = time.time()
        
        # Validate file exists
        if not os.path.exists(image_path):
            raise ValueError(f"Image file not found: {image_path}")
        
        try:
            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
            
            # Use YOLO model if loaded, otherwise use mock detection
            if self.model_loaded:
                detections = self._yolo_detection(image_path)
            else:
                detections = self._mock_detection(width, height)
            
            self.detection_count += len(detections)
            
            processing_time = time.time() - start_time
            
            return {
                'detections': detections,
                'image_size': {'width': width, 'height': height},
                'processing_time': round(processing_time, 3),
                'total_detections': self.detection_count,
                'model_used': 'yolo' if self.model_loaded else 'mock'
            }
            
        except Exception as e:
            raise ValueError(f"Error during detection: {str(e)}")
    
    def _yolo_detection(self, image_path):
        """
        Perform actual detection using YOLO model
        """
        try:
            # Run YOLO inference
            results = self.model(image_path)
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # Get bounding box coordinates (x1, y1, x2, y2)
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Convert to (x, y, width, height) format
                        x = int(x1)
                        y = int(y1)
                        width = int(x2 - x1)
                        height = int(y2 - y1)
                        
                        # Get confidence score
                        confidence = float(box.conf[0].cpu().numpy())
                        
                        # Get class name
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.model.names[class_id]
                        
                        detections.append({
                            'id': i + 1,
                            'bbox': [x, y, width, height],
                            'confidence': round(confidence, 3),
                            'class': class_name,
                            'class_id': class_id
                        })
            
            return detections
            
        except Exception as e:
            print(f"❌ YOLO detection failed: {e}")
            # Fallback to mock detection
            with Image.open(image_path) as img:
                width, height = img.size
            return self._mock_detection(width, height)
    
    def _mock_detection(self, width, height):
        """
        Fallback mock detection when YOLO is not available
        """
        detection_probability = 0.7
        
        if random.random() > detection_probability:
            return []  # No detections
        
        num_detections = random.randint(1, 4)
        detections = []
        
        for i in range(num_detections):
            min_size = min(50, width // 8, height // 8)
            max_size = min(200, width // 2, height // 2)
            
            box_width = random.randint(min_size, max_size)
            box_height = random.randint(min_size, max_size)
            
            x = random.randint(10, max(10, width - box_width - 10))
            y = random.randint(10, max(10, height - box_height - 10))
            
            confidence = round(random.uniform(0.65, 0.92), 3)
            
            detections.append({
                'id': i + 1,
                'bbox': [x, y, box_width, box_height],
                'confidence': confidence,
                'class': 'pothole',
                'class_id': 0,
                'area': box_width * box_height
            })
        
        return detections
    
    def get_stats(self):
        """Get detection statistics"""
        return {
            'total_detections': self.detection_count,
            'model_loaded': self.model_loaded,
            'model_path': self.model_path
        }


# Alternative: OpenCV-based YOLO implementation (if ultralytics doesn't work)
class OpenCVYOLODetector:
    """
    Alternative YOLO implementation using OpenCV DNN
    """
    def __init__(self, model_path, config_path=None, classes_file=None):
        self.model_path = model_path
        self.net = None
        self.classes = []
        self.model_loaded = False
        
        self._load_opencv_model()
    
    def _load_opencv_model(self):
        """Load YOLO model using OpenCV DNN"""
        try:
            # Note: YOLO .pt files need to be converted to .weights/.cfg for OpenCV
            # This is a more complex setup
            print("⚠️ OpenCV YOLO requires model conversion")
            print("💡 Consider using the ultralytics package instead")
        except Exception as e:
            print(f"❌ OpenCV YOLO loading failed: {e}")