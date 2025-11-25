import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  withCredentials: true,  // Enable cookies
});

export const detectPotholes = async (uploadData) => {
  const formData = new FormData();
  formData.append('image', uploadData.file);
  
  // Add location data if available
  if (uploadData.location) {
    formData.append('location', JSON.stringify(uploadData.location));
  }
  
  // Add timestamp
  if (uploadData.timestamp) {
    formData.append('timestamp', uploadData.timestamp);
  }

  try {
    const response = await api.post('/detect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.error || 'Detection failed');
    }
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.error || 'Server error');
    } else if (error.request) {
      throw new Error('Cannot connect to server. Please make sure the backend is running.');
    } else {
      throw new Error('An unexpected error occurred');
    }
  }
};

export const detectPotholesFromUrl = async (imageUrl) => {
  try {
    const response = await api.post('/detect/url', {
      url: imageUrl
    });

    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.error || 'Detection failed');
    }
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.error || 'Server error');
    } else if (error.request) {
      throw new Error('Cannot connect to server');
    } else {
      throw new Error('An unexpected error occurred');
    }
  }
};

export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('Backend service is unavailable');
  }
};

export const getModelInfo = async () => {
  try {
    const response = await api.get('/model/info');
    return response.data;
  } catch (error) {
    throw new Error('Could not fetch model information');
  }
};