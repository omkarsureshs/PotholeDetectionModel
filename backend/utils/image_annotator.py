from PIL import Image, ImageDraw, ImageFont
import os
import uuid

class ImageAnnotator:
    def __init__(self):
        self.output_dir = 'annotated_results'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def annotate_image(self, image_path, detections, output_path=None):
        """Annotate image with detection bounding boxes"""
        try:
            # Open the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create drawing context
                draw = ImageDraw.Draw(img)
                
                # Try to load a font
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                
                # Draw each detection
                for detection in detections:
                    bbox = detection['bbox']
                    confidence = detection['confidence']
                    
                    # Draw bounding box
                    x, y, w, h = bbox
                    draw.rectangle([x, y, x + w, y + h], outline="green", width=3)
                    
                    # Draw label background
                    label = f"Pothole: {confidence:.1%}"
                    label_bbox = draw.textbbox((x, y), label, font=font)
                    label_width = label_bbox[2] - label_bbox[0] + 10
                    label_height = label_bbox[3] - label_bbox[1] + 10
                    
                    draw.rectangle([x, y - label_height, x + label_width, y], fill="green")
                    
                    # Draw label text
                    draw.text((x + 5, y - label_height + 5), label, fill="white", font=font)
                
                # Save the annotated image
                if not output_path:
                    output_path = os.path.join(self.output_dir, f"annotated_{uuid.uuid4()}.jpg")
                
                img.save(output_path)
                return output_path
                
        except Exception as e:
            raise ValueError(f"Error annotating image: {str(e)}")

# Global annotator instance
annotator = ImageAnnotator()