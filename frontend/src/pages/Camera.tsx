import React, { useState, useEffect, useRef } from 'react';
import { Camera, Mic, Settings, Volume2, MonitorStop, AlertCircle } from 'lucide-react';
import './Camera.css';

const InterviewPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    async function getMedia() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error('Error accessing webcam: ', err);
      }
    }

    getMedia();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Top Bar */}
      <div className="top-bar">
        <div className="top-bar-content">
          <div className="flex items-center">
            <span className="title">Technical Interview Practice</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="timer-display">
              <div className="recording-indicator"></div>
              <span className="text-sm text-white">25:31</span>
            </div>
            <button className="text-white hover:text-gray-300">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-73px)]">
        {/* Main Video Area */}
        <div className="flex-1 p-6">
          <div className="video-container">
            {/* Main Video Feed */}
            <div className="video-feed">
              <video ref={videoRef} autoPlay className="w-full h-full object-cover" />
            </div>

            {/* Video Controls */}
            <div className="video-controls">
              <div className="flex items-center space-x-4">
                <button
                  className={`control-button ${isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-indigo-500 hover:bg-indigo-600'}`}
                  onClick={() => setIsRecording(!isRecording)}
                >
                  {isRecording ? (
                    <MonitorStop className="w-6 h-6 text-white" />
                  ) : (
                    <Camera className="w-6 h-6 text-white" />
                  )}
                </button>
                <button
                  className={`control-button ${isMuted ? 'bg-gray-600' : 'bg-gray-700'} hover:bg-gray-600`}
                  onClick={() => setIsMuted(!isMuted)}
                >
                  <Mic className="w-6 h-6 text-white" />
                </button>
                <button className="control-button bg-gray-700 hover:bg-gray-600">
                  <Volume2 className="w-6 h-6 text-white" />
                </button>
              </div>
            </div>

            {/* End Session Button */}
            <button className="end-session-button">End Session</button>
          </div>
        </div>

        {/* Feedback Panel */}
        <div className="feedback-panel">
          <div className="h-full flex flex-col">
            <div className="mb-4">
              <h2 className="text-lg font-medium text-white mb-2">Real-time Feedback</h2>
              <div className="space-y-4">
                {/* Speaking Pace */}
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-300">Speaking Pace</span>
                    <span className="text-sm text-gray-300">145 wpm</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-animate w-4/5 bg-green-500"></div>
                  </div>
                </div>

                {/* Eye Contact */}
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-300">Eye Contact</span>
                    <span className="text-sm text-gray-300">Good</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-animate w-3/4 bg-green-500"></div>
                  </div>
                </div>

                {/* Voice Clarity */}
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-300">Voice Clarity</span>
                    <span className="text-sm text-gray-300">Clear</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-animate w-5/6 bg-green-500"></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Suggestions */}
            <div className="flex-1 overflow-y-auto">
              <h3 className="text-sm font-medium text-gray-400 mb-3">Live Suggestions</h3>
              <div className="space-y-3">
                <div className="feedback-alert">
                  <div className="flex items-start">
                    <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5" />
                    <p className="ml-2 text-sm text-gray-300">
                      Try to slow down slightly when explaining technical concepts.
                    </p>
                  </div>
                </div>
                <div className="feedback-alert">
                  <div className="flex items-start">
                    <AlertCircle className="w-5 h-5 text-green-500 mt-0.5" />
                    <p className="ml-2 text-sm text-gray-300">
                      Good use of hand gestures to emphasize key points.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Current Question */}
            <div className="current-question">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Current Question</h3>
              <p className="text-sm text-gray-400">
                Can you explain a challenging technical problem you've solved and walk me through your problem-solving approach?
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewPage;
