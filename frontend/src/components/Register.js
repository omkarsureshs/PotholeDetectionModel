import React, { useState } from 'react';
import './Auth.css';

const Register = ({ onRegister, onSwitchToLogin, backendAvailable, apiBaseUrl = true }) => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: ''
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

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',  // Enable cookies
        body: JSON.stringify({
          email: formData.email,
          username: formData.username,
          password: formData.password
        }),
      });

      // Handle non-JSON responses
      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error('Backend server returned an invalid response. Please check if the server is running.');
        }
      }

      const data = await response.json();

      if (response.ok) {
        // Auto-login after successful registration
        const loginResponse = await fetch(`${apiBaseUrl}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',  // Enable cookies
          body: JSON.stringify({
            email: formData.email,
            password: formData.password
          }),
        });

        if (!loginResponse.ok) {
          const loginContentType = loginResponse.headers.get('content-type');
          if (!loginContentType || !loginContentType.includes('application/json')) {
            throw new Error('Registration successful but auto-login failed. Please log in manually.');
          }
        }

        const loginData = await loginResponse.json();

        if (loginResponse.ok) {
          onRegister(loginData.user);
        } else {
          setError('Registration successful! Please log in.');
          onSwitchToLogin();
        }
      } else {
        setError(data.error || 'Registration failed');
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
        <h2>Create Account</h2>
        <p className="auth-subtitle">Join the Pothole Detection community</p>
        
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
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="Choose a username"
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
              placeholder="Enter your password (min. 6 characters)"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              placeholder="Confirm your password"
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
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>
        
        <div className="auth-switch">
          Already have an account?{' '}
          <button onClick={onSwitchToLogin} className="switch-button" disabled={loading}>
            Sign in
          </button>
        </div>

        <div className="server-info">
          <small>Server: {backendAvailable ? '✅ Connected' : '❌ Disconnected'}</small>
        </div>
      </div>
    </div>
  );
};

export default Register;