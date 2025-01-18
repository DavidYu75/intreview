import React from 'react';
import './Results.css';

const ResultsPage = () => {
  return (
    <div className="results-container">
      <h1>Interview Results</h1>
      <div className="results-content">
        <div className="result-item">
          <h2>Speaking Pace</h2>
          <p>145 wpm</p>
        </div>
        <div className="result-item">
          <h2>Eye Contact</h2>
          <p>Good</p>
        </div>
        <div className="result-item">
          <h2>Voice Clarity</h2>
          <p>Clear</p>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
