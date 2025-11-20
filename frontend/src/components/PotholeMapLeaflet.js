import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './PotholeMapLeaflet.css';

// Fix for default markers in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const PotholeMapLeaflet = ({ detectionResult, onPotholeSelect }) => {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [viewMode, setViewMode] = useState('markers');
  const [statistics, setStatistics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize Map
  useEffect(() => {
    if (!mapRef.current) return;

    const initialMap = L.map(mapRef.current).setView([40.7128, -74.0060], 12);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(initialMap);

    setMap(initialMap);
    loadStatistics();

    // Cleanup function
    return () => {
      if (initialMap) {
        initialMap.remove();
      }
    };
  }, []);

  // Load statistics
  const loadStatistics = async () => {
    try {
      const response = await fetch('/api/map/statistics');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  };

  // Create custom markers with severity colors
  const createCustomIcon = (severity) => {
    const color = {
      high: '#ff4444',
      medium: '#ffaa00',
      low: '#44ff44'
    }[severity] || '#ffaa00';

    return L.divIcon({
      className: 'custom-pothole-marker',
      html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });
  };

  // Toggle view mode
  const toggleViewMode = () => {
    const newMode = viewMode === 'markers' ? 'heatmap' : 'markers';
    setViewMode(newMode);
    // For now, we'll just show markers. Heatmap can be added later.
  };

  // Save detection to map
  const saveToMap = async () => {
    if (!detectionResult) return;

    try {
      const response = await fetch('/api/map/save-detection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detection_data: detectionResult })
      });

      if (response.ok) {
        alert('✅ Detection saved to map!');
        loadStatistics();
      }
    } catch (error) {
      console.error('Error saving to map:', error);
      alert('❌ Failed to save detection to map');
    }
  };

  return (
    <div className="pothole-map-container">
      <div className="map-controls">
        <button 
          onClick={toggleViewMode}
          className={`view-toggle ${viewMode}`}
          disabled={isLoading}
        >
          {viewMode === 'markers' ? '🔍 Show Heatmap' : '📍 Show Markers'}
        </button>

        {detectionResult && detectionResult.location && (
          <button onClick={saveToMap} className="save-button" disabled={isLoading}>
            💾 Save to Map
          </button>
        )}

        {isLoading && <div className="loading-indicator">Loading pothole data...</div>}
      </div>

      {statistics && (
        <div className="map-statistics">
          <h4>Area Statistics</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{statistics.total_potholes}</span>
              <span className="stat-label">Total Potholes</span>
            </div>
            <div className="stat-item">
              <span className="stat-value" style={{color: '#ff4444'}}>
                {statistics.high_severity}
              </span>
              <span className="stat-label">High Severity</span>
            </div>
            <div className="stat-item">
              <span className="stat-value" style={{color: '#ffaa00'}}>
                {statistics.medium_severity}
              </span>
              <span className="stat-label">Medium</span>
            </div>
            <div className="stat-item">
              <span className="stat-value" style={{color: '#44ff44'}}>
                {statistics.low_severity}
              </span>
              <span className="stat-label">Low</span>
            </div>
          </div>
        </div>
      )}

      <div ref={mapRef} className="pothole-map-leaflet" />
      
      <div className="map-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color high"></span>
            High Severity
          </div>
          <div className="legend-item">
            <span className="legend-color medium"></span>
            Medium Severity
          </div>
          <div className="legend-item">
            <span className="legend-color low"></span>
            Low Severity
          </div>
        </div>
      </div>
    </div>
  );
};

export default PotholeMapLeaflet;