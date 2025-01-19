import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Volume2 } from 'lucide-react';
import './Camera.css';

const CameraPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [time, setTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    async function getMedia() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: true,
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: false, // Disable automatic gain control
            sampleRate: 48000 // Higher sample rate for better quality
          }
        });
        
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          // Prevent audio feedback
          videoRef.current.muted = true;
        }

        // Set up audio analysis
        audioContextRef.current = new AudioContext();
        analyserRef.current = audioContextRef.current.createAnalyser();
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
        // Don't connect to audio destination to prevent feedback
        // source.connect(audioContextRef.current.destination);

        // Set up MediaRecorder
        mediaRecorderRef.current = new MediaRecorder(stream);
        mediaRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        // Start monitoring audio levels
        monitorAudioLevel();
      } catch (err) {
        console.error('Error accessing media devices: ', err);
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
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    const updateLevel = () => {
      analyserRef.current?.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      const normalizedLevel = average / 255; // 0 to 1
      setAudioLevel(normalizedLevel);
      requestAnimationFrame(updateLevel);
    };

    updateLevel();
  };

  const handleRecording = async () => {
    if (isRecording) {
      // Stop recording
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        await new Promise(resolve => {
          if (mediaRecorderRef.current) {
            mediaRecorderRef.current.onstop = resolve;
          }
        });

        // Stop all tracks and clear video
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
        if (videoRef.current) {
          videoRef.current.srcObject = null;
        }

        // Create audio file and send to backend
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'interview.wav');

        try {
          // Send to backend for analysis
          const response = await fetch('http://localhost:8000/api/analyze', {
            method: 'POST',
            body: formData,
          });

          if (response.ok) {
            const results = await response.json();
            localStorage.setItem('interviewResults', JSON.stringify(results));
            navigate('/results');
          }
        } catch (error) {
          console.error('Error analyzing speech:', error);
        }
      }
    } else {
      // Start new recording
      audioChunksRef.current = [];
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.start();
      }
      setTime(0);
      timerRef.current = setInterval(() => {
        setTime(prevTime => prevTime + 1);
      }, 1000);
    }
    setIsRecording(!isRecording);
  };

  const handleMute = () => {
    if (streamRef.current) {
      const isCurrentlyMuted = isMuted;
      streamRef.current.getAudioTracks().forEach(track => {
        track.enabled = isCurrentlyMuted; // Mute or unmute based on current state
      });
      setIsMuted(!isCurrentlyMuted); // Update the state after toggling
    }
  };
  

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const getBorderColor = (level: number) => {
    if (level < 0.05) return 'border-transparent';
    return 'border-green-500';
  };

  return (
    <div className="container">
      <div className="main-content">
        {/* Video Area */}
        <div className="video-section">
          <div className={`video-feed ${getBorderColor(audioLevel)}`}>
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
              onClick={handleMute}
            >
              <Mic className={`icon ${isMuted ? 'text-red-500' : ''}`} />
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
          <h1 className="main-header">Behavioral Interview Practice</h1>
          <div className="header-divider"></div>

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
