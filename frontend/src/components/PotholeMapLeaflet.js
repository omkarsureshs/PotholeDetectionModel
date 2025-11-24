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
  const [userStats, setUserStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [userPotholes, setUserPotholes] = useState([]);
  const [allPotholes, setAllPotholes] = useState([]);
  const [showUserPotholesOnly, setShowUserPotholesOnly] = useState(false);
  const [showStatistics, setShowStatistics] = useState(false);

  const potholeLayerRef = useRef(null);
  const heatmapLayerRef = useRef(null);
  const API_BASE = 'http://localhost:5000/api';

  // Initialize Map
  useEffect(() => {
    if (!mapRef.current) return;

    // Start with Bangalore (where potholes are) - will move to user location after geolocation
    const initialMap = L.map(mapRef.current).setView([13.3752, 77.0967], 13);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(initialMap);

    setMap(initialMap);
    
    // Load initial data (try browser geolocation first, fallback to API)
    initUserLocation(initialMap);
    loadStatistics();
    loadUserStats();
    loadUserPotholes();
    fetchAndPlotGeoJSON(initialMap);

    // Set up map move event to load potholes in view
    initialMap.on('moveend', handleMapMove);

    // Cleanup function
    return () => {
      if (initialMap) {
        initialMap.off('moveend', handleMapMove);
        initialMap.remove();
      }
    };
  }, []);

  // Initialize user location: prefer browser geolocation, fallback to server IP lookup
  const initUserLocation = async (mapInstance) => {
    const setAndMarker = (loc, source = 'browser') => {
      setUserLocation(loc);

      // Helper to actually add marker and set view when the map is ready
      const addWhenReady = (m) => {
        try {
          if (!m || !loc || !loc.latitude || !loc.longitude) return;
          // use whenReady to ensure internal Leaflet structures exist
          if (typeof m.whenReady === 'function') {
            m.whenReady(() => {
              try {
                m.setView([loc.latitude, loc.longitude], 13);
                L.marker([loc.latitude, loc.longitude])
                  .addTo(m)
                  .bindPopup(`
                    <div class="user-location-popup">
                      <strong>📍 Your Location</strong><br/>
                      ${loc.city || ''}, ${loc.country || ''}<br/>
                      <small>Source: ${source}</small>
                    </div>
                  `)
                  .openPopup();
              } catch (err) {
                // swallow errors from stale/destroyed map
                console.warn('Leaflet addWhenReady error:', err);
              }
            });
          } else {
            // fallback
            m.setView([loc.latitude, loc.longitude], 13);
            L.marker([loc.latitude, loc.longitude])
              .addTo(m)
              .bindPopup(`
                <div class="user-location-popup">
                  <strong>📍 Your Location</strong><br/>
                  ${loc.city || ''}, ${loc.country || ''}<br/>
                  <small>Source: ${source}</small>
                </div>
              `)
              .openPopup();
          }
        } catch (err) {
          console.warn('Error setting user marker:', err);
        }
      };

      // If mapInstance is passed use it, else use current map state
      const m = mapInstance || map;
      if (m) addWhenReady(m);
    };

    // Try navigator.geolocation first
    if (navigator && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(async (pos) => {
        const loc = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          city: null,
          country: null,
          source: 'browser'
        };
        setAndMarker(loc, 'browser');
      }, async (err) => {
        // Fallback to server API
        try {
          const response = await fetch('http://localhost:5000/api/user/location');
          if (response.ok) {
            const location = await response.json();
            setAndMarker(location, 'server');
          }
        } catch (error) {
          console.error('Error loading user location fallback:', error);
        }
      }, { timeout: 5000 });
    } else {
      // No geolocation support, fallback to API
      try {
        const response = await fetch('http://localhost:5000/api/user/location');
        if (response.ok) {
          const location = await response.json();
          setAndMarker(location, 'server');
        }
      } catch (error) {
        console.error('Error loading user location fallback:', error);
      }
    }
  };

  // Fetch GeoJSON from backend and plot as a single layer (better performance)
  const fetchAndPlotGeoJSON = async (mapInstance) => {
    if (!mapInstance) {
      console.warn('fetchAndPlotGeoJSON: mapInstance is null');
      return;
    }
    try {
      console.log('Fetching GeoJSON from http://localhost:5000/api/map/geojson');
      const response = await fetch('http://localhost:5000/api/map/geojson?limit=500');
      
      if (!response.ok) {
        console.error('GeoJSON fetch failed with status:', response.status);
        return;
      }
      
      const geojson = await response.json();
      console.log('GeoJSON loaded with', geojson.features?.length || 0, 'features');

      // Remove previous layer
      if (potholeLayerRef.current) {
        mapInstance.removeLayer(potholeLayerRef.current);
        potholeLayerRef.current = null;
      }

      const layer = L.geoJSON(geojson, {
        pointToLayer: (feature, latlng) => {
          const severity = (feature.properties?.severity || 'medium').toLowerCase();
          const isUser = false;
          const icon = createCustomIcon(severity, isUser);
          console.log('Marker created:', {
            id: feature.properties?.id,
            severity: severity,
            lat: latlng.lat,
            lng: latlng.lng,
            coords: feature.geometry.coordinates
          });
          return L.marker(latlng, { icon: icon });
        },
        onEachFeature: (feature, markerLayer) => {
          const props = feature.properties || {};
          const popup = `
            <div class="pothole-popup">
              <div class="popup-header"><strong>🕳️ Reported Pothole</strong></div>
              <div class="popup-details">
                <div class="popup-row"><span class="label">Severity:</span> <span class="value">${(props.severity || '').toUpperCase()}</span></div>
                <div class="popup-row"><span class="label">Confidence:</span> <span class="value">${(props.confidence * 100).toFixed(1)}%</span></div>
                <div class="popup-row"><span class="label">Reported:</span> <span class="value">${props.timestamp ? new Date(props.timestamp).toLocaleString() : ''}</span></div>
              </div>
            </div>
          `;
          markerLayer.bindPopup(popup);
          markerLayer.on('click', () => onPotholeSelect && onPotholeSelect({
            id: props.id,
            latitude: feature.geometry.coordinates[1],
            longitude: feature.geometry.coordinates[0],
            ...props
          }));
        }
      }).addTo(mapInstance);

      console.log('✅ GeoJSON layer successfully added with', geojson.features?.length, 'markers');
      potholeLayerRef.current = layer;
    } catch (error) {
      console.error('Error fetching GeoJSON:', error);
    }
  };

  // Load statistics
  const loadStatistics = async () => {
    try {
      console.log('Loading statistics...');
      const response = await fetch('http://localhost:5000/api/map/statistics');
      if (response.ok) {
        const data = await response.json();
        console.log('Statistics loaded:', data);
        setStatistics(data);
      } else {
        console.error('Statistics fetch failed:', response.status);
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  };

  // Load user statistics
  const loadUserStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/user/stats');
      if (response.ok) {
        const data = await response.json();
        setUserStats(data);
      }
    } catch (error) {
      console.error('Error loading user stats:', error);
    }
  };

  // Load user's potholes
  const loadUserPotholes = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/user/potholes');
      if (response.ok) {
        const data = await response.json();
        setUserPotholes(data.potholes || []);
      }
    } catch (error) {
      console.error('Error loading user potholes:', error);
    }
  };

  // Load recent potholes (kept for API compatibility) - still supported
  const loadRecentPotholes = async (limit = 100) => {
    try {
      const response = await fetch(`http://localhost:5000/api/map/recent-potholes?limit=${limit}`);
      if (response.ok) {
        const data = await response.json();
        setAllPotholes(data.potholes || []);
        // Also update layer if needed
        if (map) {
          fetchAndPlotGeoJSON(map);
        }
      }
    } catch (error) {
      console.error('Error loading recent potholes:', error);
    }
  };

  // Load potholes in current map view
  const loadPotholesInView = async () => {
    if (!map) return;
    
    const bounds = map.getBounds();
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    
    try {
      const response = await fetch(
        `http://localhost:5000/api/map/potholes?ne_lat=${ne.lat}&ne_lng=${ne.lng}&sw_lat=${sw.lat}&sw_lng=${sw.lng}`
      );
      if (response.ok) {
        const data = await response.json();
        addPotholesToMap(data.potholes || []);
      }
    } catch (error) {
      console.error('Error loading potholes in view:', error);
    }
  };

  // Handle map movement
  const handleMapMove = () => {
    loadPotholesInView();
  };

  // Create custom markers with severity colors
  const createCustomIcon = (severity, isUserPothole = false) => {
    // Normalize severity to lowercase
    const sev = String(severity || 'medium').toLowerCase().trim();
    const color = {
      high: '#ff4444',
      medium: '#ffaa00',
      low: '#44ff44'
    }[sev] || '#ffaa00';

    const size = isUserPothole ? 24 : 20;
    const borderWidth = isUserPothole ? 4 : 3;
    const className = isUserPothole ? 'user-pothole-marker' : 'pothole-marker';

    return L.divIcon({
      className: className,
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

  // Add potholes to map
  const addPotholesToMap = (potholes) => {
    if (!map) return;

    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    const newMarkers = [];

    // Filter potholes if showing only user's potholes
    const potholesToShow = showUserPotholesOnly 
      ? potholes.filter(p => userPotholes.some(up => up.id === p.id))
      : potholes;

    potholesToShow.forEach(pothole => {
      const isUserPothole = userPotholes.some(up => up.id === pothole.id);
      
      const marker = L.marker([pothole.latitude, pothole.longitude], {
        icon: createCustomIcon(pothole.severity, isUserPothole)
      }).addTo(map);

      // Create popup content
      const popupContent = `
        <div class="pothole-popup">
          <div class="popup-header">
            <strong>${isUserPothole ? '🚗 Your Reported Pothole' : '🕳️ Reported Pothole'}</strong>
          </div>
          <div class="popup-details">
            <div class="popup-row">
              <span class="label">Severity:</span>
              <span class="value severity-${pothole.severity}">${pothole.severity.toUpperCase()}</span>
            </div>
            <div class="popup-row">
              <span class="label">Confidence:</span>
              <span class="value">${(pothole.confidence * 100).toFixed(1)}%</span>
            </div>
            <div class="popup-row">
              <span class="label">Size:</span>
              <span class="value">${Math.round(pothole.size)} px²</span>
            </div>
            <div class="popup-row">
              <span class="label">Reported:</span>
              <span class="value">${new Date(pothole.timestamp).toLocaleDateString()}</span>
            </div>
            ${!isUserPothole ? `
              <div class="popup-row">
                <span class="label">User Reports:</span>
                <span class="value">${pothole.user_reports || 1}</span>
              </div>
            ` : ''}
          </div>
          ${onPotholeSelect ? `
            <button class="popup-button" onclick="window.reactSelectPothole(${pothole.id})">
              📊 View Details
            </button>
          ` : ''}
        </div>
      `;

      marker.bindPopup(popupContent);
      
      // Add click handler for pothole selection
      if (onPotholeSelect) {
        marker.on('click', () => {
          onPotholeSelect(pothole);
        });
      }

      newMarkers.push(marker);
    });

    setMarkers(newMarkers);

    // Expose function to window for popup buttons
    window.reactSelectPothole = (potholeId) => {
      const pothole = potholes.find(p => p.id === potholeId);
      if (pothole && onPotholeSelect) {
        onPotholeSelect(pothole);
      }
    };
  };

  // Toggle view mode
  const toggleViewMode = () => {
    const newMode = viewMode === 'markers' ? 'heatmap' : 'markers';
    setViewMode(newMode);
    // For now, we'll just show markers. Heatmap can be added later.
  };

  // Toggle user potholes filter
  const toggleUserPotholesFilter = () => {
    setShowUserPotholesOnly(!showUserPotholesOnly);
  };

  // Save detection to map
  const saveToMap = async () => {
    if (!detectionResult) return;

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/map/save-detection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detection_data: detectionResult })
      });

      if (response.ok) {
        alert('✅ Detection saved to map!');
        loadStatistics();
        loadUserStats();
        loadUserPotholes();
        loadRecentPotholes();
      } else {
        alert('❌ Failed to save detection to map');
      }
    } catch (error) {
      console.error('Error saving to map:', error);
      alert('❌ Failed to save detection to map');
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh map data
  const refreshMapData = () => {
    loadStatistics();
    loadUserStats();
    loadUserPotholes();
    loadRecentPotholes();
  };

  // Center map on user location
  const centerOnUserLocation = () => {
    if (map && userLocation) {
      map.setView([userLocation.latitude, userLocation.longitude], 13);
    }
  };

  // Effect to update markers when filter changes
  useEffect(() => {
    if (allPotholes.length > 0) {
      addPotholesToMap(allPotholes);
    }
  }, [showUserPotholesOnly, userPotholes]);

  // Effect to add detection result to map
  useEffect(() => {
    if (detectionResult && detectionResult.location && map) {
      // Center map on detection location
      const { latitude, longitude } = detectionResult.location;
      map.setView([latitude, longitude], 15);
      
      // Add temporary marker for new detection
      const tempMarker = L.marker([latitude, longitude], {
        icon: createCustomIcon('medium', true)
      }).addTo(map);
      
      tempMarker.bindPopup(`
        <div class="pothole-popup">
          <div class="popup-header">
            <strong>🎯 New Detection</strong>
          </div>
          <div class="popup-details">
            <div class="popup-row">
              <span class="label">Potholes Found:</span>
              <span class="value">${detectionResult.detections.length}</span>
            </div>
            <div class="popup-row">
              <span class="label">Save to make permanent!</span>
            </div>
          </div>
        </div>
      `).openPopup();

      // Add to markers for cleanup
      setMarkers(prev => [...prev, tempMarker]);
    }
  }, [detectionResult]);

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

        <button 
          onClick={toggleUserPotholesFilter}
          className={`filter-toggle ${showUserPotholesOnly ? 'active' : ''}`}
          disabled={isLoading}
        >
          {showUserPotholesOnly ? '👤 My Potholes Only' : '👥 All Potholes'}
        </button>

        <button 
          onClick={centerOnUserLocation}
          className="location-button"
          disabled={!userLocation}
        >
          📍 My Location
        </button>

        <button 
          onClick={refreshMapData}
          className="refresh-button"
          disabled={isLoading}
        >
          🔄 Refresh
        </button>

        {detectionResult && detectionResult.location && (
          <button onClick={saveToMap} className="save-button" disabled={isLoading}>
            {isLoading ? '💾 Saving...' : '💾 Save to Map'}
          </button>
        )}

        {isLoading && <div className="loading-indicator">Loading pothole data...</div>}
      </div>

      {statistics && showStatistics && (
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
          
          {userStats && userStats.total_reports > 0 && (
            <div className="user-stats">
              <div className="user-stat-item">
                <span className="user-stat-label">Your Reports:</span>
                <span className="user-stat-value">{userStats.total_reports}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {statistics && !showStatistics && (
        <button 
          className="stats-info-button"
          onClick={() => setShowStatistics(true)}
          title="Show area statistics"
        >
          ℹ️
        </button>
      )}

      {showStatistics && (
        <button 
          className="stats-close-button"
          onClick={() => setShowStatistics(false)}
          title="Hide statistics"
        >
          ✕
        </button>
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
          <div className="legend-item user-pothole">
            <span className="legend-color user"></span>
            Your Potholes
          </div>
        </div>
        
        {showUserPotholesOnly && (
          <div className="filter-notice">
            👤 Showing only your potholes
          </div>
        )}
      </div>
    </div>
  );
};

export default PotholeMapLeaflet;