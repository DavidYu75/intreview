from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime
import logging

from app.services.video_processor import VideoProcessor
from app.services.speech_analyzer import SpeechAnalyzer
import cv2
import numpy as np
import base64

logger = logging.getLogger(__name__)

class AnalysisManager:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.speech_analyzer = SpeechAnalyzer()
        self.recorded_frames = []  # Store frames during recording

    async def process_frame(self, frame_data: str):
        """
        Decode the incoming frame data (base64), pass to VideoProcessor,
        return real-time feedback.
        """
        try:
            # Decode and store frame
            encoded_data = frame_data.split(',')[1] if ',' in frame_data else frame_data
            frame_bytes = base64.b64decode(encoded_data)
            self.recorded_frames.append(frame_bytes)

            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return {
                    "face_detected": False,
                    "attention_status": "error",
                    "sentiment": "neutral"
                }

            feedback = await self.video_processor.get_realtime_feedback(frame)
            return feedback
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return {
                "face_detected": False,
                "attention_status": "error",
                "sentiment": "neutral"
            }

    async def process_audio(self, audio_data: str):
        """
        Decode the incoming audio data (base64), pass to SpeechAnalyzer,
        return real-time feedback (like filler words, partial transcript, etc.).
        """
        try:
            encoded_data = audio_data.split(',')[1] if ',' in audio_data else audio_data
            audio_binary = base64.b64decode(encoded_data)

            feedback = await self.speech_analyzer.get_realtime_feedback(audio_binary)
            return feedback
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return {
                "text": "",
                "is_filler_word": False,
                "confidence": None
            }

    async def process_audio(self, audio_data: str):
        """Process and analyze audio chunk"""
        try:
            # Get base64 data
            encoded_data = audio_data.split(',')[1] if ',' in audio_data else audio_data
            
            # Convert to binary
            audio_binary = base64.b64decode(encoded_data)
            
            # Get real-time feedback
            feedback = await self.speech_analyzer.get_realtime_feedback(audio_binary)
            return feedback
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return {
                "text": "",
                "is_filler_word": False,
                "confidence": None
            }

    async def get_recorded_frames(self) -> List[bytes]:
        """Get all recorded frames"""
        return self.recorded_frames

    async def clear_frames(self):
        """Clear stored frames"""
        self.recorded_frames = []

    async def get_session_summary(self):
        """Get summary of the entire session"""
        video_summary = await self.video_processor.get_session_summary()
        return {
            "video_metrics": video_summary.dict()
        }

# Create a global manager
analysis_manager = AnalysisManager()

async def handle_websocket(websocket: WebSocket):
    """Main WebSocket handler"""
    logger.info("New WebSocket connection established")
    await websocket.accept()
    
    try:
        frame_count = 0
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "end_session":
                logger.info("Received end_session request")
                summary = await analysis_manager.get_session_summary()
                logger.info(f"Session summary generated: {summary}")
                await websocket.send_json({
                    "type": "session_summary",
                    "data": summary
                })
                break

            if data["type"] == "video":
                frame_count += 1
                if frame_count % 30 == 0:  # Log every 30th frame
                    logger.debug(f"Processing video frame {frame_count}")
                feedback = await analysis_manager.process_frame(data["frame"])
                response = {
                    "type": "video_feedback",
                    "feedback": feedback
                }
            elif data["type"] == "audio":
                feedback = await analysis_manager.process_audio(data["audio"])
                response = {
                    "type": "audio_feedback",
                    "feedback": feedback
                }
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass