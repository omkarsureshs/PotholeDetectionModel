import React, { useState } from 'react';
import './Auth.css';

const Login = ({ onLogin, onSwitchToRegister, backendAvailable, apiBaseUrl = true }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!backendAvailable) {
      setError('Backend server is not available. Please make sure the Flask server is running on port 5000.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',  // Enable cookies
        body: JSON.stringify(formData),
      });

      // Handle non-JSON responses (like when backend is down)
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error('Backend server returned an invalid response. Please check if the server is running.');
        }
      }

      const data = await response.json();

      if (response.ok) {
        onLogin(data.user);
      } else {
        setError(data.error || 'Login failed. Please check your credentials.');
      }
    } catch (err) {
      if (err.message.includes('Failed to fetch') || err.message.includes('Network error')) {
        setError('Cannot connect to the server. Please make sure the backend is running on port 5000.');
      } else {
        setError(err.message || 'Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Show backend warning if backend is not available
  if (!backendAvailable) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="backend-warning">
            <h3>⚠️ Server Connection Issue</h3>
            <p>The backend server is not available. Please ensure:</p>
            <ul>
              <li>Flask server is running on port 5000</li>
              <li>You've executed: <code>python app.py</code></li>
              <li>No errors in the terminal</li>
            </ul>
            <div className="warning-actions">
              <button onClick={() => window.location.reload()} className="retry-button">
                🔄 Retry Connection
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Welcome Back</h2>
        <p className="auth-subtitle">Sign in to your Pothole Detection account</p>
        
        {error && <div className="auth-error">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
              disabled={loading}
            />
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={loading || !backendAvailable}
          >
            {loading ? (
              <>
                <span className="button-spinner"></span>
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>
        
        <div className="auth-switch">
          Don't have an account?{' '}
          <button onClick={onSwitchToRegister} className="switch-button" disabled={loading}>
            Sign up
          </button>
        </div>

        <div className="server-info">
          <small>Server: {backendAvailable ? '✅ Connected' : '❌ Disconnected'}</small>
        </div>
      </div>
    </div>
  );
};

export default Login;