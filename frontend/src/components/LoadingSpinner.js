import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="loading-spinner">
      <div className="spinner"></div>
      <h3>Analyzing Image for Potholes...</h3>
      <p>This may take a few seconds</p>
    </div>
  );
};

export default LoadingSpinner;