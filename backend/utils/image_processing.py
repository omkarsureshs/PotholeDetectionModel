from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

def preprocess_image_for_model(image_path, target_size=(416, 416)):
    """
    Preprocess image for ML model using Pillow
    """
    with Image.open(image_path) as img:
        # Convert to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize
        img_resized = img.resize(target_size)
        
        # Convert to numpy array and normalize
        img_array = np.array(img_resized) / 255.0
        
        # Add batch dimension
        img_batch = np.expand_dims(img_array, axis=0)
    
    return img_batch

def visualize_detections(image_path, detections, output_path=None):
    """
    Draw bounding boxes on image using Pillow
    """
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        
        # Try to use a font
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            confidence = detection['confidence']
            
            # Draw bounding box
            draw.rectangle([x, y, x+w, y+h], outline='green', width=3)
            
            # Draw label background
            label = f"Pothole: {confidence:.1%}"
            draw.rectangle([x, y-25, x+120, y], fill='green')
            
            # Draw label text
            draw.text((x+5, y-20), label, fill='white', font=font)
        
        # Save or return the image
        if output_path:
            img.save(output_path)
            return output_path
        else:
            return img

def save_detection_result(original_image_path, detections, output_dir='results'):
    """
    Save detection results as a new image with bounding boxes
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    original_name = os.path.basename(original_image_path)
    name, ext = os.path.splitext(original_name)
    output_path = os.path.join(output_dir, f"{name}_detected{ext}")
    
    # Create and save visualization
    visualize_detections(original_image_path, detections, output_path)
    
    return output_path