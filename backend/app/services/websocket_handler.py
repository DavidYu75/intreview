from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime

from app.services.video_processor import VideoProcessor
from app.services.speech_analyzer import SpeechAnalyzer
import cv2
import numpy as np
import base64

class AnalysisManager:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.speech_analyzer = SpeechAnalyzer()

    async def process_frame(self, frame_data: str):
        """Process and analyze video frame"""
        try:
            # Process frame for real-time feedback
            encoded_data = frame_data.split(',')[1] if ',' in frame_data else frame_data
            
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
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

# Create a global manager
analysis_manager = AnalysisManager()

async def handle_websocket(websocket: WebSocket):
    """Main WebSocket handler"""
    await websocket.accept()
    
    try:
        while True:
            # Receive and process messages
            data = await websocket.receive_json()
            response = {}
            
            if data["type"] == "video":
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