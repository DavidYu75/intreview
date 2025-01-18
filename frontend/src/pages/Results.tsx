import React from 'react';
import { ArrowLeft, Mic, Camera, Clock, BarChart, Download } from 'lucide-react';
import './Results.css';

const ResultsPage = () => {
  return (
    <div className="results-container">
      {/* Header */}
      <header className="results-header">
        <button className="back-button">
          <ArrowLeft className="icon" />
          Back to Dashboard
        </button>
        <div className="header-info">
          <h1 className="title">Technical Interview Results</h1>
          <p className="date">January 15, 2025 • 45 minutes</p>
        </div>
        <button className="download-button">
          <Download className="icon" />
          Download Report
        </button>
      </header>

      <main className="main-content">
        {/* Overall Performance */}
        <section className="overall-performance section-card">
          <h2 className="section-title">Overall Performance</h2>
          <div className="performance-grid">
            <div className="performance-chart">
              <svg className="chart-svg" viewBox="0 0 36 36">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#6366F1"
                  strokeWidth="3"
                  strokeDasharray="85, 100"
                />
                <text x="18" y="20.35" className="score-text" textAnchor="middle" fill="#111827">85%</text>
              </svg>
            </div>
            <div className="performance-details">
              <div>
                <p className="metric-title">Technical Skills</p>
                <p className="metric-value">90%</p>
              </div>
              <div>
                <p className="metric-title">Communication</p>
                <p className="metric-value">82%</p>
              </div>
              <div>
                <p className="metric-title">Body Language</p>
                <p className="metric-value">83%</p>
              </div>
            </div>
          </div>
        </section>

        {/* Speech and Visual Analysis */}
        <div className="analysis-section">
          <section className="speech-analysis section-card">
            <h2 className="section-title">Speech Analysis</h2>
            <div className="analysis-metrics">
              <div className="analysis-item">
                <p className="metric-title">Speaking Pace</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: '80%' }}></div>
                </div>
                <p className="metric-value">145 wpm</p>
              </div>
              <div className="analysis-item">
                <p className="metric-title">Filler Words</p>
                <div className="progress-bar">
                  <div className="progress yellow" style={{ width: '60%' }}></div>
                </div>
                <p className="metric-value">12 instances</p>
              </div>
              <div className="analysis-item">
                <p className="metric-title">Voice Clarity</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: '90%' }}></div>
                </div>
                <p className="metric-value">92%</p>
              </div>
            </div>
          </section>

          <section className="visual-analysis section-card">
            <h2 className="section-title">Visual Analysis</h2>
            <div className="analysis-metrics">
              <div className="analysis-item">
                <p className="metric-title">Eye Contact</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: '76%' }}></div>
                </div>
                <p className="metric-value">76%</p>
              </div>
              <div className="analysis-item">
                <p className="metric-title">Hand Gestures</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: '80%' }}></div>
                </div>
                <p className="metric-value">80%</p>
              </div>
              <div className="analysis-item">
                <p className="metric-title">Posture</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: '85%' }}></div>
                </div>
                <p className="metric-value">85%</p>
              </div>
            </div>
          </section>
        </div>

        {/* Key Moments */}
        <section className="key-moments section-card">
          <h2 className="section-title">Key Moments</h2>
          <ul className="moments-list">
            <li>
              <Clock className="icon moment-icon" />
              <span>02:15 - Strong Technical Response</span>
            </li>
            <li>
              <Clock className="icon moment-icon" />
              <span>15:30 - Filler Words Detected</span>
            </li>
            <li>
              <Clock className="icon moment-icon" />
              <span>32:45 - Strong Communication</span>
            </li>
          </ul>
          <div className="video-player-container">
            <video 
              className="video-player"
              controls
              playsInline
            >
              <source src="" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </section>

        {/* Recommendations */}
        <section className="recommendations section-card">
          <h2 className="section-title">Recommendations</h2>
          <ul className="recommendations-list">
            <li>
              <BarChart className="icon rec-icon" />
              <span>Use clear examples and maintain better eye contact for improved engagement.</span>
            </li>
            <li>
              <Mic className="icon rec-icon" />
              <span>Speak at a slightly slower pace for complex topics and take deliberate pauses.</span>
            </li>
            <li>
              <Camera className="icon rec-icon" />
              <span>Continue good use of hand gestures to emphasize points effectively.</span>
            </li>
          </ul>
        </section>
      </main>
    </div>
  );
};

export default ResultsPage;
