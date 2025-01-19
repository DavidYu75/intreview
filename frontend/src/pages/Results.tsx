import React, { useState, useEffect, useRef } from 'react';
// Add these imports
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Mic, Camera, Clock, BarChart, Download } from 'lucide-react';
import './Results.css';

interface KeyMoment {
  timestamp: number;
  type: 'technical' | 'communication';
  description: string;
}

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
  key_moments: KeyMoment[];
  video_url: string;
}

const getSentimentDescription = (score: number): string => {
  if (score >= 90) return 'Very Positive';
  if (score >= 75) return 'Positive';
  return 'Neutral';  // Default state is now neutral
};

const getFillersScore = (fillerCount: number, durationMinutes: number) => {
  if (durationMinutes === 0) return 100; // Avoid division by zero
  
  const fillersPerMinute = fillerCount / durationMinutes;
  if (fillersPerMinute === 0) return 100; // Perfect case, no fillers
  
  if (fillersPerMinute <= 2) {
    // Smoothly scale from 100 down to 90 for FPM in [0, 2]
    return 100 - (fillersPerMinute / 2) * 10;
  }
  
  // Gradual decrease for FPM > 2 using exponential decay
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
  if (deviation > 50) return 'red';    // More than 50 WPM off from ideal
  if (deviation > 25) return 'yellow'; // 25-50 WPM off from ideal
  return 'green';                      // Within 25 WPM of ideal
};

const getSpeakingPacePercentage = (wpm: number) => {
  // Define the range (50 to 250 WPM is full scale)
  const minWPM = 50;
  const maxWPM = 250;
  const range = maxWPM - minWPM;
  
  // Calculate percentage (150 WPM should be at 50% of that range)
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

// Calculate an overall speech score
const calculateSpeechScore = (results: InterviewResults): number => {
  // Weight each speech metric
  const weights = {
    speechIntelligibility: 0.4,  // 40% weight
    fillerWords: 0.3,           // 30% weight
    speakingPace: 0.3           // 30% weight
  };

  // Closer to 150 wpm => higher pace score
  const idealWPM = 150;
  const paceDeviation = Math.abs(results.words_per_minute - idealWPM);
  const paceScore = Math.max(0, 100 - (paceDeviation / 2));

  // Filler words score
  const fillerScore = getFillersScore(results.filler_word_count, results.duration_minutes);

  // Combine scores with weights
  const weightedScore = 
    (results.speech_intelligibility * 100) * weights.speechIntelligibility +
    fillerScore * weights.fillerWords +
    paceScore * weights.speakingPace;

  return Math.round(weightedScore);
};

// Calculate an overall visual score
const calculateVisualScore = (results: InterviewResults): number => {
  // Base from eye contact + posture
  const baseScore = (results.eye_contact + results.posture) / 2;

  // Sentiment modifier:
  // - Neutral (0-74): no bonus
  // - Positive (75-100): up to 10% bonus
  let sentimentModifier = 1.0; // default for neutral
  if (results.sentiment >= 75) {
    const bonus = (results.sentiment - 75) / 25; // Maps 75-100 to 0-1
    sentimentModifier = 1 + (bonus * 0.1);       // up to 1.1 (10% bonus)
  }

  // Apply sentiment; cap at 100
  const finalScore = Math.min(100, baseScore * sentimentModifier);
  return Math.round(finalScore);
};

const ResultsPage = () => {
  const [results, setResults] = useState<InterviewResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

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

        // Add hardcoded key moments
        const hardcodedKeyMoments: KeyMoment[] = [
          {
            timestamp: 45,
            type: 'communication',
            description: 'Positive sentiment spike'
          },
          {
            timestamp: 128,
            type: 'communication',
            description: 'Eye contact lost'
          },
          {
            timestamp: 195,
            type: 'technical',
            description: 'Multiple Filler Words ("Um, Like")'
          }
        ];

        const processedResults = {
          ...parsedResults,
          eye_contact: parsedResults.eye_contact ?? 0,
          sentiment: parsedResults.sentiment ?? 0,
          posture: parsedResults.posture ?? 0,
          key_moments: hardcodedKeyMoments,  // Use our hardcoded moments
          video_url: parsedResults.video_url ?? '',
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

  const seekToMoment = (timestamp: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp;
      videoRef.current.play();
    }
  };

  const handleDownload = async () => {
    if (!contentRef.current || !results) return;

    try {
      const contentElement = contentRef.current;
      const canvas = await html2canvas(contentElement, {
        scale: 2,
        useCORS: true,
        logging: false,
      });

      const imgWidth = 208; // A4 width in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      const pdf = new jsPDF('p', 'mm', 'a4');
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, imgWidth, imgHeight);

      const date = new Date(results.interview_date).toLocaleDateString();
      pdf.save(`Interview-Results-${date}.pdf`);
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
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

  // Calculate interview duration in minutes
  const durationMinutes = results.duration_minutes;

  // 1) Compute the integer percentage for speech intelligibility
  const speechIntPercentage = Math.round(results.speech_intelligibility * 100);

  // 2) Compute circumference based on the path's radius
  const radius = 17.9155;
  const circumference = 2 * Math.PI * radius;

  // 3) Compute dash length
  const dashLength = (speechIntPercentage / 100) * circumference;

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
        <button className="download-button" onClick={handleDownload}>
          <Download className="icon" />
          Download Report
        </button>
      </header>

      {/* Add ref to the main content */}
      <main className="main-content" ref={contentRef}>
        {/* Overall Performance */}
        <section className="overall-performance section-card">
          <h2 className="section-title">Overall Performance</h2>
          <div className="performance-grid">
            {/* Donut Chart */}
            <div className="performance-chart">
              <svg className="chart-svg" viewBox="0 0 40 40">
                {/* Background circle */}
                <path
                  d="M20 2.0845
                     a 17.9155 17.9155 0 0 1 0 35.831
                     a 17.9155 17.9155 0 0 1 0 -35.831"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="2.5"
                />
                {/* Foreground arc (dynamic) */}
                <path
                  d="M20 2.0845
                     a 17.9155 17.9155 0 0 1 0 35.831
                     a 17.9155 17.9155 0 0 1 0 -35.831"
                  fill="none"
                  stroke="#6366F1"
                  strokeWidth="2.5"
                  strokeDasharray={`${dashLength} ${circumference - dashLength}`}
                  strokeLinecap="round"
                />
                <text 
                  x="20" 
                  y="21.5"
                  className="score-text"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#111827"
                >
                  {speechIntPercentage}%
                </text>
              </svg>
            </div>

            {/* Performance Details */}
            <div className="performance-details">
              <div className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Speech Analysis</p>
                <p className="metric-value">
                  {results ? `${calculateSpeechScore(results)}%` : '0%'}
                </p>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Visual Analysis</p>
                <p className="metric-value">
                  {results ? `${calculateVisualScore(results)}%` : '0%'}
                </p>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Content</p>
                <p className="metric-value">100%</p>
              </div>
            </div>
          </div>
        </section>

        {/* Speech and Visual Analysis */}
        <div className="analysis-section">
          <section className="speech-analysis section-card">
            <h2 className="section-title">Speech Analysis</h2>
            <div className="analysis-metrics">
              {/* Speaking Pace */}
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

              {/* Filler Words */}
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

              {/* Speech Intelligibility */}
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
              {(['eye_contact', 'posture'] as const).map((metric) => (
                <div key={metric} className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                  <p className="metric-title">
                    {metric
                      .split('_')
                      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(' ')}
                  </p>
                  <div className="progress-bar">
                    <div 
                      className={`progress ${getProgressColor(results[metric] || 0)}`}
                      style={{ width: `${results[metric] || 0}%` }}
                    ></div>
                  </div>
                  <p className="metric-value">{results[metric]?.toFixed(1) || '0'}%</p>
                </div>
              ))}
              <div className="analysis-item bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors">
                <p className="metric-title">Sentiment</p>
                <div className="progress-bar">
                  <div 
                    className="progress sentiment-progress"
                    style={{ width: `${results.sentiment}%` }}
                  ></div>
                </div>
                <p className="metric-value">{getSentimentDescription(results.sentiment)}</p>
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
                ref={videoRef}
                className="video-player"
                controls
                playsInline
              >
                <source src={results.video_url} type="video/webm" />
                Your browser does not support the video tag.
              </video>
            </div>
            <ul className="moments-list">
              {results.key_moments?.length > 0 ? (
                results.key_moments.map((moment, index) => (
                  <li 
                    key={index}
                    onClick={() => seekToMoment(moment.timestamp)}
                    className="cursor-pointer hover:bg-slate-100 transition-colors"
                  >
                    <Clock className="icon moment-icon" />
                    <div className="flex flex-col">
                      <span className="font-medium">
                        {new Date(moment.timestamp * 1000).toISOString().substr(14, 5)} - {moment.description}
                      </span>
                    </div>
                  </li>
                ))
              ) : (
                <li className="text-gray-500 text-center">
                  No key moments detected
                </li>
              )}
            </ul>
          </div>
        </section>

        {/* Recommendations */}
        <section className="recommendations section-card">
          <h2 className="section-title">Recommendations</h2>
          <ul className="recommendations-list">
            <li className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors flex items-center gap-4">
              <BarChart className="icon rec-icon" />
              <span>Maintain better eye contact for improved engagement.</span>
            </li>
            <li className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors flex items-center gap-4">
              <Mic className="icon rec-icon" />
              <span>Speak at a slightly faster pace and take deliberate pauses.</span>
            </li>
            <li className="bg-slate-50 p-2 rounded-lg hover:bg-slate-100 transition-colors flex items-center gap-4">
              <Camera className="icon rec-icon" />
              <span>Continue good posture to emphasize professionalism.</span>
            </li>
          </ul>
        </section>

        {/* Interview Transcript */}
        <section className="transcript section-card">
          <h2 className="section-title">Interview Transcript</h2>
          <div className="transcript-content bg-slate-50 p-6 rounded-lg">
            <p className="text-gray-800">
              {results.raw_transcript}
            </p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default ResultsPage;
