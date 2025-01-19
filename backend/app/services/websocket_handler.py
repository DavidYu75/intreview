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
        
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_sessions[session_id] = websocket
        
    def disconnect(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            
    async def process_frame(self, frame_data: str, session_id: str):
        try:
            encoded_data = frame_data.split(',')[1] if ',' in frame_data else frame_data
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None or frame.size == 0:
                return {
                    "face_detected": False,
                    "attention_status": "error"
                }
            
            feedback = await self.video_processor.get_realtime_feedback(frame)
            return feedback
            
        except Exception as e:
            return {
                "face_detected": False,
                "attention_status": "error"
            }

# Create a global session manager
session_manager = InterviewSessionManager()

async def handle_websocket(websocket: WebSocket, session_id: str):
    await session_manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            response = {"session_id": session_id}
            
            if data["type"] == "video":
                feedback = await session_manager.process_frame(
                    data["frame"],
                    session_id
                )
                response["type"] = "video_feedback"
                response["feedback"] = feedback
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        session_manager.disconnect(session_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        session_manager.disconnect(session_id)