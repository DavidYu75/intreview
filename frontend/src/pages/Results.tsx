import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Mic, Camera, Clock, BarChart, Download } from 'lucide-react';
import './Results.css';

interface InterviewResults {
  words_per_minute: number;
  filler_word_count: number;
  speech_intelligibility: number;
  confidence: number;
  raw_transcript: string;
  filler_words: Array<{
    word: string;
    timestamp: number;
    type: string;
  }>;
}

const ResultsPage = () => {
  const [results, setResults] = useState<InterviewResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const storedResults = localStorage.getItem('interviewResults');
    if (storedResults) {
      setResults(JSON.parse(storedResults));
      setIsLoading(false);
    } else {
      navigate('/'); // Redirect if no results
    }
  }, [navigate]);

  if (isLoading || !results) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing your interview...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="results-container">
      {/* Header */}
      <header className="results-header">
        <button className="back-button" onClick={() => navigate('/')}>
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
              <svg className="chart-svg" viewBox="0 0 40 40">  {/* Increased from 36 36 for better proportions */}
                <path
                  d="M20 2.0845 a 17.9155 17.9155 0 0 1 0 35.831 a 17.9155 17.9155 0 0 1 0 -35.831"  /* Adjusted coordinates */
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="2.5"  /* Adjusted for better visual at larger size */
                />
                <path
                  d="M20 2.0845 a 17.9155 17.9155 0 0 1 0 35.831 a 17.9155 17.9155 0 0 1 0 -35.831"  /* Adjusted coordinates */
                  fill="none"
                  stroke="#6366F1"
                  strokeWidth="2.5"  /* Adjusted for better visual at larger size */
                  strokeDasharray="85, 100"
                />
                <text 
                  x="20" 
                  y="21.5" /* Adjusted from 22 to 24 to move text down slightly */
                  className="score-text" 
                  textAnchor="middle" 
                  dominantBaseline="middle" /* Added for better vertical centering */
                  fill="#111827"
                >
                  {Math.round(results.speech_intelligibility * 100)}%
                </text>
              </svg>
            </div>
            <div className="performance-details">
              <div className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Technical Skills</p>
                <p className="metric-value">90%</p>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Communication</p>
                <p className="metric-value">82%</p>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
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
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Speaking Pace</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: `${Math.min(100, (results.words_per_minute / 170) * 100)}%` }}></div>
                </div>
                <p className="metric-value">{Math.round(results.words_per_minute)} wpm</p>
              </div>
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Filler Words</p>
                <div className="progress-bar">
                  <div className="progress yellow" style={{ width: '60%' }}></div>
                </div>
                <p className="metric-value">12 instances</p>
              </div>
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Speech Intelligibility</p>
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
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Eye Contact</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: '76%' }}></div>
                </div>
                <p className="metric-value">76%</p>
              </div>
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Hand Gestures</p>
                <div className="progress-bar">
                  <div className="progress green" style={{ width: '80%' }}></div>
                </div>
                <p className="metric-value">80%</p>
              </div>
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
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
          <div className="key-moments-container">
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
          </div>
        </section>

        {/* Recommendations */}
        <section className="recommendations section-card">
          <h2 className="section-title">Recommendations</h2>
          <ul className="recommendations-list">
            <li className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors flex items-center gap-4">
              <BarChart className="icon rec-icon" />
              <span>Use clear examples and maintain better eye contact for improved engagement.</span>
            </li>
            <li className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors flex items-center gap-4">
              <Mic className="icon rec-icon" />
              <span>Speak at a slightly slower pace for complex topics and take deliberate pauses.</span>
            </li>
            <li className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors flex items-center gap-4">
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
