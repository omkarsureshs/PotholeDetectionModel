import React, { useRef, useState, useEffect } from 'react';

const ImageUploader = ({ onImageUpload }) => {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [imageUrl, setImageUrl] = useState('');
  const [activeTab, setActiveTab] = useState('upload');
  const [location, setLocation] = useState(null);
  const [locationEnabled, setLocationEnabled] = useState(false);

  // Get user location
  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
          setLocationEnabled(true);
        },
        (error) => {
          console.error('Error getting location:', error);
          setLocationEnabled(false);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        }
      );
    }
  };

  useEffect(() => {
    getLocation();
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (files) => {
    const file = files[0];
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert('Please upload a valid image file (JPEG, PNG, GIF, WebP)');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Please upload an image smaller than 10MB');
      return;
    }

    // Create object with file and location data
    const uploadData = {
      file: file,
      location: location,
      timestamp: new Date().toISOString()
    };

    onImageUpload(uploadData);
  };

  const handleWebImage = async () => {
    if (!imageUrl.trim()) {
      alert('Please enter an image URL');
      return;
    }

    if (!isImageUrl(imageUrl)) {
      alert('Please enter a valid image URL (must end with .jpg, .png, .gif, etc.)');
      return;
    }

    try {
      // Convert URL to File object
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      
      // Create file from blob
      const file = new File([blob], 'web-image.jpg', { type: blob.type });
      
      // Validate file
      if (file.size > 10 * 1024 * 1024) {
        alert('Image is too large (max 10MB)');
        return;
      }

      const uploadData = {
        file: file,
        location: location,
        timestamp: new Date().toISOString()
      };

      onImageUpload(uploadData);
      setImageUrl('');
    } catch (error) {
      alert('Failed to load image from URL. Please check the URL and try again.');
      console.error('Error loading web image:', error);
    }
  };

  const isImageUrl = (url) => {
    return /\.(jpeg|jpg|gif|png|webp)$/.test(url.toLowerCase()) || 
           url.startsWith('data:image/') ||
           url.includes('images.unsplash.com') ||
           url.includes('picsum.photos');
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  const handleUrlChange = (e) => {
    setImageUrl(e.target.value);
  };

  const handleUrlKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleWebImage();
    }
  };

  return (
    <div className="image-uploader">
      {/* Location Status */}
      <div className="location-status">
        <div className={`location-indicator ${locationEnabled ? 'enabled' : 'disabled'}`}>
          {locationEnabled ? '📍' : '❌'} 
          GPS: {locationEnabled ? 
            `Enabled (${location?.latitude?.toFixed(4) || 'N/A'}, ${location?.longitude?.toFixed(4) || 'N/A'})` : 
            'Disabled - No location data'
          }
        </div>
        <button 
          onClick={getLocation} 
          className="location-refresh-btn"
          title="Refresh location"
        >
          🔄
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="upload-tabs">
        <button 
          className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          📁 Upload File
        </button>
        <button 
          className={`tab-button ${activeTab === 'web' ? 'active' : ''}`}
          onClick={() => setActiveTab('web')}
        >
          🌐 Web Image
        </button>
      </div>

      {/* File Upload Tab */}
      {activeTab === 'upload' && (
        <div
          className={`upload-area ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="upload-content">
            <div className="upload-icon">📁</div>
            <h3>Upload Road Image</h3>
            <p>Drag & drop, paste, or click to browse</p>
            <p className="file-info">Supports: JPG, PNG, GIF, WebP • Max: 10MB</p>
            <p className="paste-hint">💡 Try pasting an image (Ctrl+V)</p>
            
            <button 
              type="button" 
              onClick={onButtonClick}
              className="browse-button"
            >
              Browse Files
            </button>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleChange}
            style={{ display: 'none' }}
          />
        </div>
      )}

      {/* Web Image Tab */}
      {activeTab === 'web' && (
        <div className="web-image-area">
          <div className="web-image-content">
            <div className="upload-icon">🌐</div>
            <h3>Web Image URL</h3>
            <p>Paste image URL or enter manually</p>
            
            <div className="url-input-container">
              <input
                type="url"
                placeholder="https://example.com/image.jpg"
                value={imageUrl}
                onChange={handleUrlChange}
                onKeyPress={handleUrlKeyPress}
                className="url-input"
              />
              <button 
                onClick={handleWebImage}
                className="load-url-button"
                disabled={!imageUrl.trim()}
              >
                Load Image
              </button>
            </div>

            <div className="url-examples">
              <p><strong>Supported URLs:</strong></p>
              <ul>
                <li>Direct image links (.jpg, .png, .gif)</li>
                <li>Unsplash images</li>
                <li>Picsum photos</li>
                <li>Base64 data URLs</li>
              </ul>
            </div>

            <p className="paste-hint">💡 Try pasting an image URL (Ctrl+V)</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageUploader;