import React, { useRef, useEffect, useState } from 'react';
import { generatePDFReport } from '../services/pdfService';

const DetectionResult = ({ imageUrl, detectionResult, onReset }) => {
  const canvasRef = useRef(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [generatingPDF, setGeneratingPDF] = useState(false);
  const [showBackendImage, setShowBackendImage] = useState(false);

  // Severity color mapping
  const severityColors = {
    high: '#ff4444',
    medium: '#ffaa00', 
    low: '#44ff44'
  };

  const severityIcons = {
    high: '🔴',
    medium: '🟡',
    low: '🟢'
  };

  useEffect(() => {
    if (imageUrl && detectionResult) {
      drawDetections();
    }
  }, [imageUrl, detectionResult]);

  const drawDetections = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      setImageDimensions({ width: img.width, height: img.height });

      // Draw detections with severity-based colors
      detectionResult.detections.forEach((detection, index) => {
        const [x, y, width, height] = detection.bbox;
        const confidence = detection.confidence;
        
        // Get severity level (with fallback)
        const severityLevel = detection.severity?.level || 'medium';
        const color = severityColors[severityLevel] || '#00ff00';

        // Draw bounding box with severity color
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.strokeRect(x, y, width, height);

        // Draw label background
        ctx.fillStyle = color;
        const label = `${severityIcons[severityLevel]} ${(confidence * 100).toFixed(1)}%`;
        const textWidth = ctx.measureText(label).width;
        
        const labelX = Math.max(0, Math.min(x, canvas.width - textWidth - 10));
        const labelY = Math.max(25, y);
        
        ctx.fillRect(labelX, labelY - 25, textWidth + 10, 25);

        // Draw label text
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 14px Arial';
        ctx.fillText(label, labelX + 5, labelY - 8);
      });
    };

    img.onerror = () => {
      console.error('Failed to load image for detection drawing');
    };

    img.src = imageUrl;
  };

  const downloadResult = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const link = document.createElement('a');
    link.download = `pothole-detection-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  const downloadBackendImage = () => {
    if (!detectionResult.annotated_image) return;
    
    const link = document.createElement('a');
    link.download = `pothole-detection-backend-${Date.now()}.jpg`;
    link.href = `data:image/jpeg;base64,${detectionResult.annotated_image}`;
    link.click();
  };

  const handlePDFGeneration = async () => {
    setGeneratingPDF(true);
    try {
      // Use backend annotated image if available, otherwise use canvas
      let annotatedImage;
      if (detectionResult.annotated_image) {
        annotatedImage = `data:image/jpeg;base64,${detectionResult.annotated_image}`;
      } else {
        const canvas = canvasRef.current;
        annotatedImage = canvas.toDataURL('image/png');
      }
      
      await generatePDFReport(detectionResult, annotatedImage);
    } catch (error) {
      alert('Failed to generate PDF report: ' + error.message);
    } finally {
      setGeneratingPDF(false);
    }
  };

  // Count severities safely
  const getSeverityCount = (level) => {
    return detectionResult.detections.filter(d => 
      d.severity && d.severity.level === level
    ).length;
  };

  // Check if backend annotated image is available
  const hasBackendImage = detectionResult.annotated_image;

  return (
    <div className="detection-result">
      <div className="result-header">
        <h2>Detection Results</h2>
        <div className="result-stats">
          <span className="stat">
            Potholes Found: <strong>{detectionResult.detections.length}</strong>
          </span>
          <span className="stat">
            High Severity: <strong style={{color: '#ff4444'}}>
              {getSeverityCount('high')}
            </strong>
          </span>
          <span className="stat">
            Medium Severity: <strong style={{color: '#ffaa00'}}>
              {getSeverityCount('medium')}
            </strong>
          </span>
          <span className="stat">
            Low Severity: <strong style={{color: '#44ff44'}}>
              {getSeverityCount('low')}
            </strong>
          </span>
        </div>
      </div>

      {/* Severity Summary - Only show if we have detections */}
      {detectionResult.detections.length > 0 && (
        <div className="severity-summary">
          <h3>Severity Analysis</h3>
          <div className="severity-cards">
            <div className="severity-card high">
              <span className="severity-icon">🔴</span>
              <span className="severity-count">
                {getSeverityCount('high')}
              </span>
              <span className="severity-label">High Priority</span>
              <span className="severity-description">Immediate attention needed</span>
            </div>
            <div className="severity-card medium">
              <span className="severity-icon">🟡</span>
              <span className="severity-count">
                {getSeverityCount('medium')}
              </span>
              <span className="severity-label">Medium Priority</span>
              <span className="severity-description">Schedule repair</span>
            </div>
            <div className="severity-card low">
              <span className="severity-icon">🟢</span>
              <span className="severity-count">
                {getSeverityCount('low')}
              </span>
              <span className="severity-label">Low Priority</span>
              <span className="severity-description">Monitor condition</span>
            </div>
          </div>
        </div>
      )}

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
            <div className="image-header">
              <h3>Detection Result</h3>
              {hasBackendImage && (
                <div className="image-toggle">
                  <button 
                    onClick={() => setShowBackendImage(!showBackendImage)}
                    className="toggle-button"
                  >
                    {showBackendImage ? '🔄 Show Frontend' : '🔄 Show Backend'}
                  </button>
                </div>
              )}
            </div>
            <div className="image-container">
              {showBackendImage && hasBackendImage ? (
                // Show backend annotated image
                <img 
                  src={`data:image/jpeg;base64,${detectionResult.annotated_image}`}
                  alt="Backend Annotated Detection" 
                  className="result-image"
                  style={{ 
                    maxWidth: '100%', 
                    height: 'auto',
                    border: '2px solid #007bff',
                    borderRadius: '8px'
                  }}
                />
              ) : (
                // Show frontend canvas
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
              )}
            </div>
            <div className="image-actions">
              {showBackendImage && hasBackendImage ? (
                <button onClick={downloadBackendImage} className="download-button small">
                  📥 Download Backend Image
                </button>
              ) : (
                <button onClick={downloadResult} className="download-button small">
                  📥 Download Frontend Image
                </button>
              )}
              {hasBackendImage && (
                <div className="image-source">
                  <small>
                    {showBackendImage 
                      ? 'Showing: Backend Annotated Image' 
                      : 'Showing: Frontend Canvas Drawing'
                    }
                  </small>
                </div>
              )}
            </div>
          </div>
        </div>

        {detectionResult.detections.length > 0 && (
          <div className="detections-list">
            <h3>Detailed Analysis:</h3>
            <div className="detections-grid">
              {detectionResult.detections.map((detection, index) => {
                const severity = detection.severity || { level: 'medium', score: 0.5, description: 'Severity analysis pending' };
                
                return (
                  <div key={detection.id || index} className={`detection-item ${severity.level}`}>
                    <div className="detection-header">
                      <span className="detection-id">
                        {severityIcons[severity.level]} Pothole #{index + 1}
                      </span>
                      <span className={`severity-badge ${severity.level}`}>
                        {severity.level.toUpperCase()}
                      </span>
                    </div>
                    <div className="detection-info">
                      <span className="confidence">
                        Confidence: <strong>{(detection.confidence * 100).toFixed(1)}%</strong>
                      </span>
                      <span className="severity-score">
                        Severity Score: <strong>{(severity.score * 100).toFixed(1)}</strong>
                      </span>
                    </div>
                    <div className="detection-details">
                      <div className="detection-bbox">
                        Size: {detection.bbox[2]}×{detection.bbox[3]}px 
                        (Area: {detection.bbox[2] * detection.bbox[3]}px²)
                      </div>
                      <div className="severity-description">
                        {severity.description}
                      </div>
                      {detection.location && (
                        <div className="detection-location">
                          📍 {detection.location.latitude?.toFixed(6) || 'N/A'}, {detection.location.longitude?.toFixed(6) || 'N/A'}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
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
        <button 
          onClick={handlePDFGeneration} 
          className="pdf-button"
          disabled={generatingPDF || detectionResult.detections.length === 0}
        >
          {generatingPDF ? (
            <>
              <span className="pdf-loading"></span>
              Generating PDF...
            </>
          ) : (
            '📄 Generate PDF Report'
          )}
        </button>
        <button onClick={onReset} className="reset-button">
          🔄 Analyze Another Image
        </button>
      </div>
    </div>
  );
};

export default DetectionResult;