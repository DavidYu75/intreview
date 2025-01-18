import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Volume2 } from 'lucide-react';
import './Camera.css';

const CameraPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [time, setTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function getMedia() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error('Error accessing webcam: ', err);
      }
    }

    getMedia();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const handleRecording = () => {
    if (isRecording) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      console.log(`Interview ended at ${time} seconds`);
      navigate('/results');
    } else {
      setTime(0);
      timerRef.current = setInterval(() => {
        setTime(prevTime => prevTime + 1);
      }, 1000);
    }
    setIsRecording(!isRecording);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className="container">
      <div className="camera-top-bar">
        <h2>Behavioral Interview Practice</h2>
      </div>
      <div className="main-content">
        {/* Video Area */}
        <div className="video-section">
          <div className="video-feed">
            <video ref={videoRef} autoPlay className="video"></video>
            {isRecording && (
              <div className="recording-indicator">
                <div className="indicator-dot"></div>
                <span>{formatTime(time)}</span>
              </div>
            )}
          </div>
          <div className="video-controls">
            <button
              className={`control-button ${isMuted ? 'muted' : ''}`}
              onClick={() => setIsMuted(!isMuted)}
            >
              <Mic className="icon" />
            </button>
            <button className="control-button">
              <Volume2 className="icon" />
            </button>
          </div>
          <button
            className={`end-session-button ${isRecording ? 'end' : 'start'}`}
            onClick={handleRecording}
          >
            {isRecording ? 'End Session' : 'Start Intreview'}
          </button>
        </div>

        {/* Feedback Panel */}
        <div className="feedback-panel">
          <h3 className="panel-header">Current Question</h3>
          <div className="panel-section">
            <p>
              Can you explain a challenging technical problem you've solved and walk me through your problem-solving approach?
            </p>
          </div>

          <h3 className="panel-header">Real-time Feedback</h3>
          <div className="panel-section">
            <div className="feedback-metrics">
              <div className="metric">
                <div className="metric-label">
                  <span>Speaking Pace</span>
                  <span>145 wpm</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-bar-fill" style={{ width: '80%' }}></div>
                </div>
              </div>
              <div className="metric">
                <div className="metric-label">
                  <span>Eye Contact</span>
                  <span>Good</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-bar-fill" style={{ width: '75%' }}></div>
                </div>
              </div>
              <div className="metric">
                <div className="metric-label">
                  <span>Voice Clarity</span>
                  <span>Clear</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-bar-fill" style={{ width: '90%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraPage;
