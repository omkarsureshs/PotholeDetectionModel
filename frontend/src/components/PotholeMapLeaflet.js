import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './PotholeMapLeaflet.css';

// Load heatmap CSS if needed
const loadHeatmapCSS = () => {
  const linkId = 'heatmap-css';
  if (!document.getElementById(linkId)) {
    const link = document.createElement('link');
    link.id = linkId;
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet-heat@0.2.0/dist/leaflet-heat.css';
    document.head.appendChild(link);
  }
};

// Load HeatmapLayer library for heatmap visualization
const loadHeatmapScript = () => {
  return new Promise((resolve) => {
    if (window.L && window.L.heatLayer) {
      console.log('✅ Heatmap library already loaded');
      resolve();
      return;
    }
    console.log('📥 Loading heatmap library...');
    
    // Try multiple CDN sources in order of reliability
    const cdnSources = [
      'https://unpkg.com/leaflet-heat@0.2.0/dist/leaflet-heat.js',
      'https://cdnjs.cloudflare.com/ajax/libs/leaflet-heat/0.2.0/leaflet-heat.js',
      'https://www.leafletjs.com/examples/heat/Leaflet.heat.js'
    ];
    
    let currentIndex = 0;
    
    const loadNext = () => {
      if (currentIndex >= cdnSources.length) {
        console.error('❌ Could not load heatmap from any CDN source');
        resolve(); // Continue anyway, heatmap will just be unavailable
        return;
      }
      
      const script = document.createElement('script');
      script.src = cdnSources[currentIndex];
      
      script.onload = () => {
        if (window.L && window.L.heatLayer) {
          console.log(`✅ Heatmap library loaded from: ${cdnSources[currentIndex]}`);
          resolve();
        } else {
          console.warn(`⚠️ Script loaded but L.heatLayer not found, trying next source...`);
          currentIndex++;
          loadNext();
        }
      };
      
      script.onerror = () => {
        console.warn(`⚠️ Failed to load from ${cdnSources[currentIndex]}, trying next...`);
        currentIndex++;
        loadNext();
      };
      
      document.head.appendChild(script);
    };
    
    loadNext();
  });
};

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
  const [userStats, setUserStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [userPotholes, setUserPotholes] = useState([]);
  const [allPotholes, setAllPotholes] = useState([]);
  const [showUserPotholesOnly, setShowUserPotholesOnly] = useState(false);
  const [showStatistics, setShowStatistics] = useState(false);

  const potholeLayerRef = useRef(null);
  const heatmapLayerRef = useRef(null);

  // Create custom markers with severity colors
  const createCustomIcon = (severity, isUserPothole = false) => {
    const sev = String(severity || 'medium').toLowerCase().trim();
    const color = {
      high: '#ff4444',
      medium: '#ffaa00',
      low: '#44ff44'
    }[sev] || '#ffaa00';

    const size = isUserPothole ? 24 : 20;
    const borderWidth = isUserPothole ? 4 : 3;

    return L.divIcon({
      html: `
        <div style="
          background-color: ${color}; 
          width: ${size}px; 
          height: ${size}px; 
          border-radius: 50%; 
          border: ${borderWidth}px solid white; 
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          cursor: pointer;
        "></div>
      `,
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
    });
  };

  // Initialize Map
  useEffect(() => {
    if (!mapRef.current || map) return;

    console.log('🗺️ Initializing Leaflet map...');
    
    // Create map
    const initialMap = L.map(mapRef.current).setView([13.3752, 77.0967], 13);

    // Add tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(initialMap);

    // Load heatmap script
    loadHeatmapScript().then(() => {
      console.log('✅ Heatmap library loaded');
    });

    setMap(initialMap);
    console.log('✅ Map initialized');

    // Cleanup
    return () => {
      if (initialMap) {
        initialMap.remove();
      }
    };
  }, []);

  // Load statistics from backend
  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/map/statistics');
        if (response.ok) {
          const data = await response.json();
          console.log('📊 Statistics:', data);
          setStatistics(data);
        }
      } catch (error) {
        console.error('Error loading statistics:', error);
      }
    };
    loadStats();
  }, []);

  // Fetch and display GeoJSON potholes
  useEffect(() => {
    if (!map) return;

    const fetchPotholes = async () => {
      try {
        console.log('🔄 Fetching GeoJSON...');
        const response = await fetch('http://localhost:5000/api/map/geojson?limit=500');
        
        if (!response.ok) {
          console.error('❌ GeoJSON fetch failed:', response.status);
          return;
        }
        
        const geojson = await response.json();
        console.log(`✅ Got ${geojson.features?.length || 0} potholes`);

        // Convert to pothole array
        const potholesArray = geojson.features.map(f => ({
          id: f.properties.id,
          latitude: f.geometry.coordinates[1],
          longitude: f.geometry.coordinates[0],
          severity: (f.properties.severity || 'medium').toLowerCase(),
          confidence: f.properties.confidence,
          timestamp: f.properties.timestamp,
        }));
        
        setAllPotholes(potholesArray);

        // Remove previous layer
        if (potholeLayerRef.current) {
          map.removeLayer(potholeLayerRef.current);
        }

        // Create a feature group to hold all markers (fixed positions)
        const featureGroup = L.featureGroup();

        // Add each pothole as a fixed marker
        geojson.features.forEach((feature) => {
          const latlng = L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);
          const severity = (feature.properties.severity || 'medium').toLowerCase();
          const props = feature.properties;
          
          const marker = L.marker(latlng, { 
            icon: createCustomIcon(severity, false),
            zIndexOffset: 0  // Keep consistent z-index
          });
          
          const popup = `
            <div class="pothole-popup">
              <strong>🕳️ Pothole</strong><br/>
              Severity: <strong>${(props.severity || 'UNKNOWN').toUpperCase()}</strong><br/>
              Confidence: <strong>${(props.confidence * 100).toFixed(1)}%</strong><br/>
              Location: ${latlng.lat.toFixed(4)}°, ${latlng.lng.toFixed(4)}°<br/>
              Reported: ${props.timestamp ? new Date(props.timestamp).toLocaleDateString() : 'N/A'}
            </div>
          `;
          
          marker.bindPopup(popup);
          marker.on('click', () => {
            console.log('Clicked pothole:', props.id, 'at', latlng);
          });
          
          featureGroup.addLayer(marker);
        });

        // Add feature group to map
        featureGroup.addTo(map);
        potholeLayerRef.current = featureGroup;
        
        console.log(`✅ Added ${geojson.features.length} fixed markers to map`);
      } catch (error) {
        console.error('❌ Error fetching potholes:', error);
      }
    };

    fetchPotholes();
  }, [map]);

  // Toggle heatmap/markers
  const toggleViewMode = () => {
    if (!map || allPotholes.length === 0) {
      console.warn('⚠️ Map or data not ready for heatmap toggle');
      alert('No pothole data available for heatmap');
      return;
    }

    const newMode = viewMode === 'markers' ? 'heatmap' : 'markers';

    try {
      if (newMode === 'heatmap') {
        // Hide markers
        if (potholeLayerRef.current && map._layers) {
          map.removeLayer(potholeLayerRef.current);
          console.log('✅ Markers hidden');
        }

        // Prepare heatmap data
        // Format: [latitude, longitude, intensity (0-1)]
        const heatmapData = allPotholes.map(p => {
          const intensity = Math.max(0.1, Math.min(1, p.confidence || 0.5));
          return [p.latitude, p.longitude, intensity];
        });
        
        console.log(`🔥 Creating heatmap with ${heatmapData.length} data points`);
        console.log('📊 Sample data:', heatmapData.slice(0, 3));

        // Check if heatmap library is available
        if (!window.L || !window.L.heatLayer) {
          console.error('❌ Heatmap library (L.heatLayer) not available');
          console.log('Available L methods:', Object.keys(window.L || {}).slice(0, 10));
          alert('Heatmap library failed to load. Please check console.');
          return;
        }

        try {
          const heatmapLayer = window.L.heatLayer(heatmapData, {
            radius: 30,
            blur: 20,
            maxZoom: 18,
            minOpacity: 0.3,
            gradient: {
              0.0: '#00ff00',    // Green - low severity
              0.5: '#ffff00',    // Yellow - medium
              0.75: '#ff8800',   // Orange - high
              1.0: '#ff0000'     // Red - critical
            }
          }).addTo(map);
          
          heatmapLayerRef.current = heatmapLayer;
          console.log('✅ Heatmap layer created and added to map');
        } catch (error) {
          console.error('❌ Error creating heatmap:', error);
          alert('Failed to create heatmap: ' + error.message);
          return;
        }
      } else {
        // Hide heatmap
        if (heatmapLayerRef.current && map._layers) {
          try {
            map.removeLayer(heatmapLayerRef.current);
            heatmapLayerRef.current = null;
            console.log('✅ Heatmap removed');
          } catch (error) {
            console.error('Error removing heatmap:', error);
          }
        }

        // Show markers
        if (potholeLayerRef.current && map._layers) {
          map.addLayer(potholeLayerRef.current);
          console.log('✅ Markers displayed');
        }
      }
    } catch (error) {
      console.error('❌ Error toggling view mode:', error);
      alert('Error changing view mode: ' + error.message);
    }

    setViewMode(newMode);
  };

  // Refresh data
  const refreshMapData = async () => {
    console.log('🔄 Refreshing...');
    if (map) {
      const response = await fetch('http://localhost:5000/api/map/geojson?limit=500');
      if (response.ok) {
        const geojson = await response.json();
        const potholesArray = geojson.features.map(f => ({
          id: f.properties.id,
          latitude: f.geometry.coordinates[1],
          longitude: f.geometry.coordinates[0],
          severity: (f.properties.severity || 'medium').toLowerCase(),
          confidence: f.properties.confidence,
          timestamp: f.properties.timestamp,
        }));
        setAllPotholes(potholesArray);
      }
    }
  };

  // Toggle fullscreen
  const toggleFullscreen = async () => {
    const mapContainer = mapRef.current;
    if (!mapContainer) return;

    try {
      if (!document.fullscreenElement) {
        await mapContainer.requestFullscreen();
        console.log('📺 Fullscreen enabled');
        // Trigger map resize after fullscreen transition
        setTimeout(() => {
          try {
            if (map && map._container) {
              map.invalidateSize();
            }
          } catch (err) {
            console.warn('Map resize warning:', err.message);
          }
        }, 500);
      } else {
        await document.exitFullscreen();
        console.log('📺 Fullscreen disabled');
        setTimeout(() => {
          try {
            if (map && map._container) {
              map.invalidateSize();
            }
          } catch (err) {
            console.warn('Map resize warning:', err.message);
          }
        }, 500);
      }
    } catch (error) {
      console.error('Fullscreen error:', error);
    }
  };

  // Save all potholes to map
  const saveToMap = async () => {
    try {
      setIsLoading(true);
      console.log('💾 Saving potholes to map...');
      
      // Save each pothole
      for (const pothole of allPotholes) {
        await fetch('http://localhost:5000/api/map/save-detection', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            detection_data: {
              location: {
                latitude: pothole.latitude,
                longitude: pothole.longitude
              },
              detections: [{
                severity: pothole.severity,
                confidence: pothole.confidence,
                timestamp: pothole.timestamp
              }]
            }
          })
        });
      }
      
      alert(`✅ Successfully saved ${allPotholes.length} potholes to map!`);
      console.log('✅ All potholes saved');
    } catch (error) {
      console.error('Error saving to map:', error);
      alert('❌ Error saving potholes');
    } finally {
      setIsLoading(false);
    }
  };

  // Center on user location
  const centerOnUserLocation = () => {
    if (map && userLocation) {
      map.setView([userLocation.latitude, userLocation.longitude], 13);
    }
  };

  return (
    <div className="pothole-map-container">
      <div className="map-controls">
        <button onClick={toggleViewMode} className={`heatmap-button ${viewMode === 'heatmap' ? 'active' : ''}`} disabled={isLoading || allPotholes.length === 0}>
          {viewMode === 'markers' ? '🔥 Show Heatmap' : '📍 Show Markers'}
        </button>

        <button onClick={refreshMapData} className="refresh-button" disabled={isLoading}>
          🔄 Refresh
        </button>

        <button onClick={centerOnUserLocation} className="location-button" disabled={!userLocation}>
          📍 My Location
        </button>

        <button onClick={toggleFullscreen} className="fullscreen-button" disabled={isLoading}>
          🖥️ Fullscreen
        </button>

        <button 
          onClick={saveToMap} 
          className="save-button" 
          disabled={isLoading || allPotholes.length === 0}
        >
          {isLoading ? '💾 Saving...' : `💾 Save Map (${allPotholes.length})`}
        </button>

        {isLoading && <div className="loading-indicator">Processing...</div>}
      </div>

      {statistics && showStatistics && (
        <div className="map-statistics">
          <h4>Area Statistics</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{statistics.total_potholes}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat-item">
              <span className="stat-value" style={{color: '#ff4444'}}>
                {statistics.high_severity}
              </span>
              <span className="stat-label">High</span>
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

      {statistics && !showStatistics && (
        <button className="stats-info-button" onClick={() => setShowStatistics(true)} title="Show statistics">
          ℹ️
        </button>
      )}

      {showStatistics && (
        <button className="stats-close-button" onClick={() => setShowStatistics(false)} title="Hide statistics">
          ✕
        </button>
      )}

      <div ref={mapRef} className="pothole-map-leaflet" />

      <div className="map-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color high"></span> High
          </div>
          <div className="legend-item">
            <span className="legend-color medium"></span> Medium
          </div>
          <div className="legend-item">
            <span className="legend-color low"></span> Low
          </div>
        </div>
      </div>
    </div>
  );
};

export default PotholeMapLeaflet;
