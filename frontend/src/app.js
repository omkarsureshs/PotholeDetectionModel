import React, { useState } from 'react';
import ImageUploader from './components/ImageUploader';
import DetectionResult from './components/DetectionResult';
import LoadingSpinner from './components/LoadingSpinner';
import PotholeMapLeaflet from './components/PotholeMapLeaflet';
import { detectPotholes } from './services/api';
import './styles/App.css';

function App() {
  const [detectionResult, setDetectionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [activeTab, setActiveTab] = useState('detection');

  const handleImageUpload = async (uploadData) => {
    setLoading(true);
    setError(null);
    
    const imageUrl = URL.createObjectURL(uploadData.file);
    setSelectedImage(imageUrl);
    
    try {
      const result = await detectPotholes(uploadData);
      setDetectionResult(result);
      setActiveTab('detection');
    } catch (err) {
      setError(err.message || 'An error occurred during detection');
      setDetectionResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setDetectionResult(null);
    setSelectedImage(null);
    setError(null);
    setActiveTab('detection');
  };

  const handlePotholeSelect = (pothole) => {
    console.log('Selected pothole:', pothole);
    alert(`Pothole Details:\nSeverity: ${pothole.severity}\nConfidence: ${(pothole.confidence * 100).toFixed(1)}%\nLocation: ${pothole.latitude}, ${pothole.longitude}`);
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🚧 Pothole Detection System</h1>
          <p>AI-powered road defect detection and mapping</p>
        </div>
        
        {!loading && (
          <nav className="app-navigation">
            <button 
              className={`nav-tab ${activeTab === 'detection' ? 'active' : ''}`}
              onClick={() => setActiveTab('detection')}
            >
              🔍 Detection
            </button>
            <button 
              className={`nav-tab ${activeTab === 'map' ? 'active' : ''}`}
              onClick={() => setActiveTab('map')}
            >
              🗺️ Pothole Map
            </button>
          </nav>
        )}
      </header>

      <main className="app-main">
        {/* Detection Tab Content */}
        {activeTab === 'detection' && (
          <div className="tab-content">
            {!detectionResult && !loading && (
              <div className="upload-section">
                <ImageUploader onImageUpload={handleImageUpload} />
              </div>
            )}

            {loading && <LoadingSpinner />}

            {error && (
              <div className="error-message">
                <h3>❌ Error</h3>
                <p>{error}</p>
                <button onClick={handleReset} className="reset-button">
                  Try Again
                </button>
              </div>
            )}

            {detectionResult && selectedImage && (
              <DetectionResult
                imageUrl={selectedImage}
                detectionResult={detectionResult}
                onReset={handleReset}
              />
            )}
          </div>
        )}

        {/* Map Tab Content */}
        {activeTab === 'map' && (
          <div className="tab-content">
            <div className="map-section">
              <div className="map-header">
                <h2>🗺️ Pothole Heat Map</h2>
                <p>Visualize pothole distribution and severity across your area</p>
              </div>
              
              {/* ⚠️ THIS IS THE CHANGED PART ⚠️ */}
              <PotholeMapLeaflet 
                detectionResult={detectionResult}
                onPotholeSelect={handlePotholeSelect}
              />
              
              <div className="map-info">
                <h4>How to use the map:</h4>
                <ul>
                  <li>🔴 <strong>Red markers</strong>: High severity potholes</li>
                  <li>🟡 <strong>Yellow markers</strong>: Medium severity potholes</li>
                  <li>🟢 <strong>Green markers</strong>: Low severity potholes</li>
                  <li>🔥 <strong>Heatmap</strong>: Shows pothole density</li>
                  <li>💾 <strong>Save detections</strong>: Click "Save to Map" after detection</li>
                </ul>
                
                {!detectionResult && (
                  <div className="map-tip">
                    <p>💡 <strong>Tip:</strong> Switch to the Detection tab to analyze images and add potholes to the map.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <p>Powered by AI & React.js | Road Maintenance Assistant</p>
          <div className="footer-links">
            <span>📍 GPS Mapping</span>
            <span>📊 Severity Analysis</span>
            <span>📄 PDF Reports</span>
            <span>🗺️ Heatmap Visualization</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;