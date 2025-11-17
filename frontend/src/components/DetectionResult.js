import React, { useRef, useEffect, useState } from 'react';

const DetectionResult = ({ imageUrl, detectionResult, onReset }) => {
  const canvasRef = useRef(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (imageUrl && detectionResult) {
      drawDetections();
    }
  }, [imageUrl, detectionResult]);

  const drawDetections = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Create a new image to load
    const img = new Image();
    img.crossOrigin = 'anonymous'; // Handle CORS if needed
    
    img.onload = () => {
      // Set canvas dimensions to match the image
      canvas.width = img.width;
      canvas.height = img.height;
      
      // Clear canvas and draw the original image
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      
      // Store image dimensions for display
      setImageDimensions({ width: img.width, height: img.height });

      // Draw detections on top of the image
      detectionResult.detections.forEach((detection, index) => {
        const [x, y, width, height] = detection.bbox;
        const confidence = detection.confidence;

        // Draw bounding box
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, width, height);

        // Draw label background
        ctx.fillStyle = '#00ff00';
        const label = `Pothole ${(confidence * 100).toFixed(1)}%`;
        const textWidth = ctx.measureText(label).width;
        
        // Ensure label stays within canvas bounds
        const labelX = Math.max(0, Math.min(x, canvas.width - textWidth - 10));
        const labelY = Math.max(15, y);
        
        ctx.fillRect(labelX, labelY - 20, textWidth + 10, 20);

        // Draw label text
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(label, labelX + 5, labelY - 5);
      });
    };

    img.onerror = () => {
      console.error('Failed to load image for detection drawing');
    };

    img.src = imageUrl;
  };

  const downloadResult = () => {
    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.download = `pothole-detection-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  return (
    <div className="detection-result">
      <div className="result-header">
        <h2>Detection Results</h2>
        <div className="result-stats">
          <span className="stat">
            Potholes Found: <strong>{detectionResult.detections.length}</strong>
          </span>
          <span className="stat">
            Processing Time: <strong>{detectionResult.processing_time}s</strong>
          </span>
          <span className="stat">
            Image Size: <strong>{imageDimensions.width} × {imageDimensions.height}px</strong>
          </span>
          <span className="stat">
            Model: <strong>{detectionResult.model_used.toUpperCase()}</strong>
          </span>
        </div>
      </div>

      <div className="result-content">
        <div className="image-comparison">
          <div className="image-section">
            <h3>Original Image</h3>
            <div className="image-container">
              <img 
                src={imageUrl} 
                alt="Original" 
                className="result-image"
              />
            </div>
          </div>
          
          <div className="image-section">
            <h3>Detection Result</h3>
            <div className="image-container">
              <canvas
                ref={canvasRef}
                className="detection-canvas"
                style={{ 
                  maxWidth: '100%', 
                  height: 'auto',
                  border: '2px solid #00ff00',
                  borderRadius: '8px'
                }}
              />
            </div>
          </div>
        </div>

        {detectionResult.detections.length > 0 && (
          <div className="detections-list">
            <h3>Detected Potholes:</h3>
            <div className="detections-grid">
              {detectionResult.detections.map((detection, index) => (
                <div key={detection.id || index} className="detection-item">
                  <div className="detection-info">
                    <span className="detection-id">Pothole #{index + 1}</span>
                    <span className="confidence" style={{ color: '#00ff00' }}>
                      Confidence: {(detection.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="detection-bbox">
                    Position: ({detection.bbox[0]}px, {detection.bbox[1]}px) 
                    Size: {detection.bbox[2]}×{detection.bbox[3]}px
                    Area: {detection.bbox[2] * detection.bbox[3]}px²
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {detectionResult.detections.length === 0 && (
          <div className="no-detections">
            <h3>✅ No Potholes Detected</h3>
            <p>The AI model did not find any potholes in this image.</p>
            <p>Try uploading a different image with clearer road surfaces.</p>
          </div>
        )}
      </div>

      <div className="result-actions">
        <button onClick={downloadResult} className="download-button">
          📥 Download Annotated Image
        </button>
        <button onClick={onReset} className="reset-button">
          🔄 Analyze Another Image
        </button>
      </div>
    </div>
  );
};

export default DetectionResult;