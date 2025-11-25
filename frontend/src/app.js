import React, { useState, useEffect } from 'react';
import ImageUploader from './components/ImageUploader';
import DetectionResult from './components/DetectionResult';
import LoadingSpinner from './components/LoadingSpinner';
import PotholeMapLeaflet from './components/PotholeMapLeaflet';
import Login from './components/Login';
import Register from './components/Register';
import { detectPotholes } from './services/api';
import './styles/App.css';

// ✅ Add this constant at the top - FIXED URL
const API_BASE_URL = 'http://localhost:5000';

function App() {
  const [detectionResult, setDetectionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [activeTab, setActiveTab] = useState('detection');
  
  // Authentication states
  const [currentUser, setCurrentUser] = useState(null);
  const [authView, setAuthView] = useState('login');
  const [authLoading, setAuthLoading] = useState(true);
  const [backendAvailable, setBackendAvailable] = useState(true);

  // Check if backend is available and user is logged in
  useEffect(() => {
    checkBackendStatus();
  }, []);

  // Auto-refresh user stats every 5 seconds when on map tab
  useEffect(() => {
    if (!currentUser || activeTab !== 'map') return;

    const interval = setInterval(() => {
      refreshUserStats(currentUser);
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [currentUser, activeTab]);

  const checkBackendStatus = async () => {
    try {
      // ✅ FIXED: Use full URL with port 5000
      const response = await fetch(`${API_BASE_URL}/api/test`);
      if (response.ok) {
        setBackendAvailable(true);
        checkAuthStatus();
      } else {
        setBackendAvailable(false);
        setAuthLoading(false);
      }
    } catch (error) {
      console.error('Backend not available:', error);
      setBackendAvailable(false);
      setAuthLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    try {
      // ✅ FIXED: Use full URL with port 5000 and include credentials
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        credentials: 'include' // Important for cookies
      });
      
      if (!response.ok) {
        throw new Error('Auth endpoint not available');
      }
      
      const data = await response.json();
      
      if (data.user) {
        setCurrentUser(data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      // If auth fails, assume no user is logged in
      setCurrentUser(null);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogin = (user) => {
    console.log('✅ User logged in:', user);
    setCurrentUser(user);
    // Refresh user stats after login
    refreshUserStats(user);
  };

  const handleRegister = (user) => {
    console.log('✅ User registered:', user);
    setCurrentUser(user);
    // Refresh user stats after registration
    refreshUserStats(user);
  };

  const refreshUserStats = async (user) => {
    try {
      console.log('📊 Refreshing user stats...');
      const response = await fetch(`${API_BASE_URL}/api/user/stats`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const stats = await response.json();
        console.log('📊 User stats:', stats);
        
        // Update current user with fresh stats
        setCurrentUser(prev => ({
          ...prev,
          statistics: {
            total_reports: stats.total_reports || 0,
            high_severity_reports: stats.high_severity_reports || 0,
            medium_severity_reports: stats.medium_severity_reports || 0,
            low_severity_reports: stats.low_severity_reports || 0,
            reputation_points: stats.reputation_points || 0
          }
        }));
      }
    } catch (error) {
      console.error('Error refreshing user stats:', error);
    }
  };

  const handleLogout = async () => {
    try {
      // ✅ FIXED: Use full URL with port 5000 and include credentials
      await fetch(`${API_BASE_URL}/api/auth/logout`, { 
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setCurrentUser(null);
      setDetectionResult(null);
      setSelectedImage(null);
      setError(null);
    }
  };

  const switchToRegister = () => setAuthView('register');
  const switchToLogin = () => setAuthView('login');

  const handleImageUpload = async (uploadData) => {
    if (!currentUser) {
      setError('Please log in to detect potholes');
      return;
    }

    if (!backendAvailable) {
      setError('Backend server is not available. Please make sure the Flask server is running on port 5000.');
      return;
    }

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

  const retryBackendConnection = () => {
    setAuthLoading(true);
    checkBackendStatus();
  };

  // Show backend connection error
  if (!backendAvailable) {
    return (
      <div className="error-screen">
        <div className="error-content">
          <h1>🚧 Backend Server Not Available</h1>
          <p>The Flask backend server is not running or not accessible.</p>
          <div className="troubleshooting">
            <h3>To fix this:</h3>
            <ol>
              <li>Make sure your Flask server is running on port 5000</li>
              <li>Run: <code>python app.py</code> in your backend directory</li>
              <li>Check that the server starts without errors</li>
              <li>Verify you can access: <a href="http://localhost:5000/api/test" target="_blank" rel="noopener noreferrer">http://localhost:5000/api/test</a></li>
              <li>Make sure there are no other applications using port 5000</li>
            </ol>
          </div>
          <button onClick={retryBackendConnection} className="retry-button">
            🔄 Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Checking authentication...</p>
      </div>
    );
  }

  // Show authentication pages if not logged in
  if (!currentUser) {
    return (
      <div className="App">
        {authView === 'login' ? (
          <Login 
            onLogin={handleLogin} 
            onSwitchToRegister={switchToRegister}
            backendAvailable={backendAvailable}
            apiBaseUrl={API_BASE_URL} // ✅ Pass the base URL to Login component
          />
        ) : (
          <Register 
            onRegister={handleRegister}
            onSwitchToLogin={switchToLogin}
            backendAvailable={backendAvailable}
            apiBaseUrl={API_BASE_URL} // ✅ Pass the base URL to Register component
          />
        )}
      </div>
    );
  }

  // Main app content when user is logged in
  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🚧 Pothole Detection System</h1>
          <p>AI-powered road defect detection and mapping</p>
        </div>
        
        {/* User Menu */}
        <div className="user-menu">
          <div className="user-info">
            <span className="welcome-message">
              Welcome, <strong>{currentUser.username}</strong>!
            </span>
            {currentUser.statistics && (
              <span className="user-reports">
                Reports: {currentUser.statistics.total_reports || 0}
              </span>
            )}
          </div>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>

        {/* Navigation Tabs */}
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
                <ImageUploader 
                  onImageUpload={handleImageUpload}
                  currentUser={currentUser}
                />
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
                currentUser={currentUser}
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
                <div className="user-map-stats">
                  <span>Your Reports: <strong>{currentUser.statistics?.total_reports || 0}</strong></span>
                  {currentUser.statistics && (
                    <span>Reputation: <strong>{currentUser.statistics.reputation_points || 0}</strong></span>
                  )}
                </div>
              </div>
              
              <PotholeMapLeaflet 
                detectionResult={detectionResult}
                onPotholeSelect={handlePotholeSelect}
                currentUser={currentUser}
              />
              
              <div className="map-info">
                <h4>How to use the map:</h4>
                <ul>
                  <li>🔴 <strong>Red markers</strong>: High severity potholes</li>
                  <li>🟡 <strong>Yellow markers</strong>: Medium severity potholes</li>
                  <li>🟢 <strong>Green markers</strong>: Low severity potholes</li>
                  <li>🔵 <strong>Blue markers</strong>: Your reported potholes</li>
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
          <p>Powered by AI & React.js | Road Maintenance Assistant | Logged in as {currentUser.username}</p>
          <div className="footer-links">
            <span>📍 GPS Mapping</span>
            <span>📊 Severity Analysis</span>
            <span>📄 PDF Reports</span>
            <span>🗺️ Heatmap Visualization</span>
            <span>🔐 User Accounts</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;