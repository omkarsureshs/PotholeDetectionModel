import React, { useState } from 'react';
import ImageUploader from './components/ImageUploader';
import DetectionResult from './components/DetectionResult';
import LoadingSpinner from './components/LoadingSpinner';
import { detectPotholes } from './services/api';
import './styles/App.css';

function App() {
  const [detectionResult, setDetectionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);

  const handleImageUpload = async (uploadData) => {
    setLoading(true);
    setError(null);
    
    // Create object URL from the file for display
    const imageUrl = URL.createObjectURL(uploadData.file);
    setSelectedImage(imageUrl);
    
    try {
      const result = await detectPotholes(uploadData);
      setDetectionResult(result);
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
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🚧 Pothole Detection System</h1>
        <p>Upload an image to detect potholes using AI</p>
      </header>

      <main className="app-main">
        {!detectionResult && !loading && (
          <ImageUploader onImageUpload={handleImageUpload} />
        )}

        {loading && <LoadingSpinner />}

        {error && (
          <div className="error-message">
            <h3>Error</h3>
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
      </main>

      <footer className="app-footer">
        <p>Powered by AI & React.js</p>
      </footer>
    </div>
  );
}

export default App;