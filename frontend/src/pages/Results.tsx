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
  duration_minutes: number;
  interview_date: string;
  eye_contact: number; // Percentage value (e.g., 76)
  sentiment: number;   // Positive sentiment score (e.g., 80)
  posture: number;     // Posture score (e.g., 85)
}



const getFillersScore = (fillerCount: number, durationMinutes: number) => {
  if (durationMinutes === 0) return 100; // Avoid division by zero
  
  const fillersPerMinute = fillerCount / durationMinutes;

  if (fillersPerMinute === 0) return 100; // Perfect case, no fillers
  
  if (fillersPerMinute <= 2) {
    // Smoothly scale from 100 to 90 for FPM in [0, 2]
    return 100 - (fillersPerMinute / 2) * 10;
  }
  
  // Gradual decrease for FPM > 2
  // Use exponential decay: max score 90, decaying towards 20
  const adjustedFPM = fillersPerMinute - 2; // Offset to start decay after 2 FPM
  return Math.max(20, 90 * Math.exp(-adjustedFPM / 5));
};


const getProgressColor = (percentage: number) => {
  if (percentage < 40) return 'red';
  if (percentage < 75) return 'yellow';
  return 'green';
};

const getSpeakingPaceColor = (wpm: number) => {
  const idealWPM = 150;
  const deviation = Math.abs(wpm - idealWPM);
  if (deviation > 50) return 'red';  // More than 50 WPM off from ideal
  if (deviation > 25) return 'yellow';  // 25-50 WPM off from ideal
  return 'green';  // Within 25 WPM of ideal
};

const getSpeakingPacePercentage = (wpm: number) => {
  // Define the range (50 to 250 WPM is full scale)
  const minWPM = 50;
  const maxWPM = 250;
  const range = maxWPM - minWPM;
  
  // Calculate percentage (150 WPM should be at 50%)
  const percentage = ((wpm - minWPM) / range) * 100;
  
  // Clamp between 0 and 100
  return Math.max(0, Math.min(100, percentage));
};

const formatDuration = (minutes: number) => {
  if (minutes >= 1) {
    const hours = Math.floor(minutes);
    const remainingMinutes = Math.round((minutes % 1) * 60);
    return hours > 0 
      ? `${hours} hr ${remainingMinutes} min`
      : `${Math.floor(minutes)} minutes`;
  } else {
    // Convert to seconds if less than 1 minute
    return `${Math.round(minutes * 60)} seconds`;
  }
};

const ResultsPage = () => {
  const [results, setResults] = useState<InterviewResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const storedResults = localStorage.getItem('interviewResults');
        console.log('Raw stored results from localStorage:', storedResults);
        
        if (!storedResults) {
          console.error('No results found in localStorage');
          throw new Error('No results found');
        }

        const parsedResults = JSON.parse(storedResults);
        console.log('Parsed results:', parsedResults);

        // Log individual metrics
        console.log('Visual metrics:', {
          eye_contact: parsedResults.eye_contact,
          sentiment: parsedResults.sentiment,
          posture: parsedResults.posture
        });

        const processedResults = {
          ...parsedResults,
          eye_contact: parsedResults.eye_contact ?? 0,
          sentiment: parsedResults.sentiment ?? 0,
          posture: parsedResults.posture ?? 0,
        };

        console.log('Final processed results:', processedResults);
        setResults(processedResults);
      } catch (err) {
        console.error('Error processing results:', err);
      }
      setIsLoading(false);
    };

    fetchResults();
  }, [navigate]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

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

  // Calculate interview duration in minutes from the results
  const durationMinutes = results.duration_minutes;

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
          <p className="date">
            {formatDate(results.interview_date)} • {formatDuration(results.duration_minutes)}
          </p>
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
          </div>
        </section>

        {/* Speech and Visual Analysis */}
        <div className="analysis-section">
          <section className="speech-analysis section-card">
            <h2 className="section-title">Speech Analysis</h2>
            <div className="analysis-metrics">
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Speaking Pace</p>
                <div className="progress-bar-container">
                  <div className="progress-bar">
                    <div 
                      className={`progress ${getSpeakingPaceColor(results.words_per_minute)}`} 
                      style={{ width: `${getSpeakingPacePercentage(results.words_per_minute)}%` }}
                    ></div>
                    <div className="ideal-pace-marker"></div>
                  </div>
                  <p className="metric-value">{Math.round(results.words_per_minute)} wpm</p>
                </div>
              </div>
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Filler Words</p>
                <div className="progress-bar">
                  <div 
                    className={`progress ${getProgressColor(getFillersScore(results.filler_word_count, durationMinutes))}`} 
                    style={{ width: `${getFillersScore(results.filler_word_count, durationMinutes)}%` }}
                  ></div>
                </div>
                <p className="metric-value">
                  {results.filler_word_count} instances 
                  ({(results.filler_word_count / durationMinutes).toFixed(1)} per minute)
                </p>
              </div>
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Speech Intelligibility</p>
                <div className="progress-bar">
                  <div 
                    className="progress green" 
                    style={{ width: `${Math.round(results.speech_intelligibility * 100)}%` }}
                  ></div>
                </div>
                <p className="metric-value">{Math.round(results.speech_intelligibility * 100)}%</p>
              </div>
            </div>
          </section>

          <section className="visual-analysis section-card">
            <h2 className="section-title">Visual Analysis</h2>
            <div className="analysis-metrics">
              {(['eye_contact', 'sentiment', 'posture'] as const).map((metric) => (
                <div key={metric} className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                  <p className="metric-title">{metric.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</p>
                  <div className="progress-bar">
                    <div 
                      className={`progress ${getProgressColor(results[metric] || 0)}`}
                      style={{ width: `${results[metric] || 0}%` }}
                    ></div>
                  </div>
                  <p className="metric-value">{results[metric]?.toFixed(1) || '0'}%</p>
                </div>
              ))}
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

        {/* Interview Transcript (Now fullwidth and after recommendations) */}
        <section className="transcript section-card">
          <h2 className="section-title">Interview Transcript</h2>
          <div className="transcript-content bg-slate-50 p-6 rounded-lg">
            <p className="text-gray-800">  {/* Changed from text-gray-700 to text-gray-800 for better contrast */}
              {results.raw_transcript}
            </p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default ResultsPage;
