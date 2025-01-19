import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Volume2 } from 'lucide-react';
import LoadingContext from '../contexts/LoadingContext';
import './Camera.css';

const CameraPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);  // Add this line
  const [isMuted, setIsMuted] = useState(false);
  const [time, setTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);

  // Posture can be "Good" or "Poor"
  const [posture, setPosture] = useState<string>('Normal');
  // Sentiment can be "Positive", "Neutral", or anything else (e.g. "Negative")
  const [sentiment, setSentiment] = useState<string>('Neutral');
  // Eye contact is a boolean: true (Yes) / false (No)
  const [eyeContact, setEyeContact] = useState<boolean>(true);

  const wsRef = useRef<WebSocket | null>(null);  // Change ws state to ref

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const navigate = useNavigate();

  // -- Set up audio + video stream on mount --
  useEffect(() => {
    async function getMedia() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: true,
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: false, // Disable automatic gain control
            sampleRate: 48000       // Higher sample rate for better quality
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

        // Set up MediaRecorder for audio
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

    // Cleanup on unmount
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

  // -- WebSocket setup --
  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/api/ws/video');
    
    wsRef.current.onopen = () => {
      console.log('WebSocket Connected');
    };
    
    wsRef.current.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        console.log('WebSocket message received:', data);  // Debug log
        if (data.type === 'video_feedback') {
          const feedback = data.feedback;
          setPosture(feedback.attention_status === 'poor_posture' ? 'Poor' : 'Good');
          setSentiment(feedback.sentiment.charAt(0).toUpperCase() + feedback.sentiment.slice(1));
          setEyeContact(feedback.attention_status === 'centered');
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
    
    wsRef.current.onclose = (event) => {
      console.log('WebSocket Closed:', event.code, event.reason);
    };

    return () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []);

  // -- Audio volume monitoring --
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

  // -- Start / Stop recording --
  const handleRecording = async () => {
    if (isRecording) {
      setIsLoading(true);
      try {
        // Stop timer
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }

        // Get video metrics before stopping
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          console.log("Requesting final analysis...");
          wsRef.current.send(JSON.stringify({ type: "end_session" }));
          
          const videoMetrics = await new Promise((resolve) => {
            const messageHandler = (event: MessageEvent) => {
              const response = JSON.parse(event.data);
              if (response.type === "session_summary") {
                console.log("Received final metrics:", response.data);
                wsRef.current?.removeEventListener('message', messageHandler);
                resolve(response.data.video_metrics);
              }
            };
            wsRef.current?.addEventListener('message', messageHandler);
          });

          // Stop recording and create audio blob
          if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
            await new Promise<void>((resolve) => {
              if (mediaRecorderRef.current) {
                mediaRecorderRef.current.onstop = () => resolve();
              }
            });
          }

          // Process audio
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const formData = new FormData();
          formData.append('audio', audioBlob, 'interview.wav');

          // Send for analysis
          const response = await fetch('http://localhost:8000/analysis/speech', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) throw new Error('Speech analysis failed');

          const audioResults = await response.json();
          console.log("Audio analysis results:", audioResults);
          
          // Combine results
          const combinedResults = {
            ...audioResults,
            eye_contact: (videoMetrics as { eye_contact_score: number }).eye_contact_score,
            sentiment: (videoMetrics as { sentiment_score: number }).sentiment_score,
            posture: (videoMetrics as { posture_score: number }).posture_score,
          };
          
          console.log("Final combined results:", combinedResults);
          localStorage.setItem('interviewResults', JSON.stringify(combinedResults));
          
          // Navigate to results
          navigate('/results');
        }
      } catch (error) {
        console.error('Error ending session:', error);
      } finally {
        setIsLoading(false);
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.close();
        }
      }
    } else {
      // Start recording
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

  // -- Limit video frames to avoid slowdown (10 FPS example) --
  useEffect(() => {
    let lastTime = 0;
    let animationId: number;

    const captureFrame = (time: number) => {
      // If not recording or WS closed, stop
      if (!isRecording || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        cancelAnimationFrame(animationId);
        return;
      }

      const delta = time - lastTime;
      const interval = 1000 / 10; // 10 FPS (adjust as needed)

      if (delta > interval) {
        lastTime = time - (delta % interval);

        if (videoRef.current) {
          // Use a temporary canvas in-memory
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');

          // Safeguard in case video hasn't loaded dimensions yet
          const vw = videoRef.current.videoWidth || 640;
          const vh = videoRef.current.videoHeight || 480;

          canvas.width = vw;
          canvas.height = vh;
          ctx?.drawImage(videoRef.current, 0, 0, vw, vh);

          // Reduce quality a bit more to speed up
          const frameData = canvas.toDataURL('image/jpeg', 0.4);

          wsRef.current.send(JSON.stringify({ 
            type: 'video', 
            frame: frameData.split(',')[1],
          }));
        }
      }

      animationId = requestAnimationFrame(captureFrame);
    };

    if (isRecording) {
      animationId = requestAnimationFrame(captureFrame);
    }

    // Cleanup
    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [isRecording]);

  // -- Mute / Unmute --
  const handleMute = () => {
    if (streamRef.current) {
      const isCurrentlyMuted = isMuted;
      streamRef.current.getAudioTracks().forEach(track => {
        track.enabled = isCurrentlyMuted; // Toggle
      });
      setIsMuted(!isCurrentlyMuted);
    }
  };

  // -- Helpers --
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const getBorderColor = (level: number) => {
    if (level < 0.05) return 'border-transparent';
    return 'border-green-500';
  };

  // --- Logic for posture, sentiment, eye contact ---
  // Posture => "Good" => full green; "Poor" => full red
  const postureColor = posture === 'Good' ? 'green' : 'red';
  const postureWidth = '100%'; // always full

  // Sentiment => "Positive" => full green; "Neutral" => empty; else => full red
  const sLower = sentiment.toLowerCase();
  const isPositive = sLower === 'positive';
  const isNeutral = sLower === 'neutral';
  let sentimentColor = '';
  let sentimentWidth = '0%'; // default empty
  if (isPositive) {
    sentimentColor = 'green';
    sentimentWidth = '100%';
  } else if (!isNeutral) {
    // anything else => full red
    sentimentColor = 'red';
    sentimentWidth = '100%';
  }

  // Eye Contact => true => "Yes" => full green; false => "No" => full red
  const eyeContactLabel = eyeContact ? 'Yes' : 'No';
  const eyeContactColor = eyeContact ? 'green' : 'red';
  const eyeContactWidth = '100%'; // always full

  // Add loading screen
  if (isLoading) {
    return <LoadingContext />;
  }

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
              
              {/* Posture */}
              <div className="metric">
                <div className="metric-label">
                  <span>Posture</span>
                  <span>{isRecording ? posture : "Good/Poor"}</span>
                </div>
                <div className="progress-bar">
                  <div
                    className={`progress ${isRecording ? postureColor : ''}`}
                    style={{ width: isRecording ? postureWidth : '0%' }}
                  ></div>
                </div>
              </div>

              {/* Sentiment */}
              <div className="metric">
                <div className="metric-label">
                  <span>Sentiment</span>
                  <span>{isRecording ? sentiment : "Positive/Neutral"}</span>
                </div>
                <div className="progress-bar">
                  <div
                    className={`progress ${isRecording ? sentimentColor : ''}`}
                    style={{ width: isRecording ? sentimentWidth : '0%' }}
                  ></div>
                </div>
              </div>

              {/* Eye Contact */}
              <div className="metric">
                <div className="metric-label">
                  <span>Eye Contact</span>
                  <span>{isRecording ? eyeContactLabel : "Yes/No"}</span>
                </div>
                <div className="progress-bar">
                  <div
                    className={`progress ${isRecording ? eyeContactColor : ''}`}
                    style={{ width: isRecording ? eyeContactWidth : '0%' }}
                  ></div>
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
