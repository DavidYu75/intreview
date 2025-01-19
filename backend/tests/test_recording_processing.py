import asyncio
import base64
import cv2
import numpy as np
from datetime import datetime
import pytest
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.recording_storage import RecordingStorage
from app.db.models.analysis_models import AnalysisStorage
from app.services.post_processor import PostProcessor
from app.core.config import get_settings

settings = get_settings()

async def create_sample_frame():
    """Create a sample video frame with a face-like shape"""
    # Create a blank frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw a circle for the face
    cv2.circle(frame, (320, 240), 100, (200, 200, 200), -1)
    
    # Draw eyes
    cv2.circle(frame, (280, 200), 20, (255, 255, 255), -1)
    cv2.circle(frame, (360, 200), 20, (255, 255, 255), -1)
    
    # Draw mouth (slight smile)
    cv2.ellipse(frame, (320, 280), (60, 30), 0, 0, 180, (255, 255, 255), -1)
    
    # Convert to base64
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode()

async def create_sample_audio():
    """Create a sample audio chunk (silent)"""
    # Create 1 second of silent audio (44.1kHz, 16-bit, mono)
    sample_rate = 44100
    duration = 1  # seconds
    samples = np.zeros(sample_rate * duration, dtype=np.int16)
    return base64.b64encode(samples.tobytes()).decode()

async def main():
    """Test the recording and post-processing pipeline"""
    try:
        print("Starting integration test...")
        
        # Initialize services
        recording_storage = RecordingStorage(settings.MONGODB_URL, settings.DATABASE_NAME)
        analysis_storage = AnalysisStorage(recording_storage.db)
        post_processor = PostProcessor(recording_storage, analysis_storage)
        
        # Create a test session
        session_id = "test_session_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        print(f"Created test session: {session_id}")
        
        # Start recording
        recording_id = await recording_storage.start_recording(session_id)
        print(f"Started recording: {recording_id}")
        
        # Create and store sample frames and audio
        print("Storing sample data...")
        for i in range(10):  # Store 10 frames/audio chunks
            # Store video frame
            frame_data = await create_sample_frame()
            await recording_storage.store_chunk(
                recording_id,
                frame_data,
                "video",
                datetime.utcnow()
            )
            
            # Store audio chunk
            audio_data = await create_sample_audio()
            await recording_storage.store_chunk(
                recording_id,
                audio_data,
                "audio",
                datetime.utcnow()
            )
            
            print(f"Stored chunk {i+1}/10")
            await asyncio.sleep(0.1)  # Small delay between chunks
        
        # End recording
        print("Ending recording...")
        result = await recording_storage.end_recording(recording_id)
        print(f"Recording ended: {result}")
        
        # Process recording
        print("Starting post-processing...")
        analysis_id = await post_processor.process_recording(recording_id, session_id)
        print(f"Analysis completed: {analysis_id}")
        
        # Get analysis results
        print("Retrieving analysis results...")
        analysis = await analysis_storage.get_analysis(analysis_id)
        
        # Print summary
        print("\nAnalysis Summary:")
        if analysis.speech_analysis:
            print(f"Speech Analysis:")
            print(f"- Words per minute: {analysis.speech_analysis.words_per_minute}")
            print(f"- Filler words: {analysis.speech_analysis.filler_word_count}")
            print(f"- Speech intelligibility: {analysis.speech_analysis.speech_intelligibility}")
            
        if analysis.visual_analysis:
            print(f"\nVisual Analysis:")
            print(f"- Attention score: {analysis.visual_analysis.attention_score}")
            print(f"- Eye contact: {analysis.visual_analysis.eye_contact_percentage}%")
            print(f"- Posture score: {analysis.visual_analysis.posture_score}")
            print(f"- Dominant sentiment: {analysis.visual_analysis.dominant_sentiment}")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(main())