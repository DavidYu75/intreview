import { useEffect, useRef } from 'react';
import './Camera.css';

export default function Camera() {
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
    <div className="page-container">
      <h1>Camera Page</h1>
      <video ref={videoRef} autoPlay />
    </div>
  );
}


