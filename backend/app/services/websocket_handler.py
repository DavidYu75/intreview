from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.video_processor import VideoProcessor
from app.services.speech_analyzer import SpeechAnalyzer
import base64
import numpy as np
import cv2

class InterviewSessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, WebSocket] = {}
        self.video_processor = VideoProcessor()
        self.speech_analyzer = SpeechAnalyzer()
        
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_sessions[session_id] = websocket
        
    def disconnect(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            
    async def process_frame(self, frame_data: str, session_id: str):
        try:
            # Decode base64 frame
            encoded_data = frame_data.split(',')[1] if ',' in frame_data else frame_data
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Process frame using video processor
            processed_frame, metrics = await self.video_processor.process_frame(frame)
            
            # Get real-time feedback
            feedback = await self.video_processor.get_realtime_feedback(frame)
            
            # Enhance feedback with more details
            # feedback.update({
            #     "frame_shape": frame.shape if frame is not None else None,
            #     "face_position": metrics.get("face_position"),
            #     "processing_successful": True,
            #     "metrics": metrics
            # })
            
            return feedback
            
        except Exception as e:
            return {
                "error": str(e),
                "processing_successful": False,
                "face_detected": False,
                "attention_status": "error"
            }
            
    async def process_audio(self, audio_data: bytes, session_id: str):
        try:
            # Process audio chunk using speech analyzer
            feedback = await self.speech_analyzer.get_realtime_feedback(audio_data)
            return feedback
            
        except Exception as e:
            return {"error": str(e)}

# Create a global session manager
session_manager = InterviewSessionManager()

async def handle_websocket(websocket: WebSocket, session_id: str):
    await session_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive JSON message
            data = await websocket.receive_json()
            
            response = {"session_id": session_id}
            
            if data["type"] == "video":
                # Process video frame
                feedback = await session_manager.process_frame(
                    data["frame"],
                    session_id
                )
                response["type"] = "video_feedback"
                response["feedback"] = feedback
                
            elif data["type"] == "audio":
                # Process audio chunk
                feedback = await session_manager.process_audio(
                    data["audio"],
                    session_id
                )
                response["type"] = "audio_feedback"
                response["feedback"] = feedback
            
            # Send feedback back to client
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        session_manager.disconnect(session_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        session_manager.disconnect(session_id)

