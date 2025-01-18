from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from services.video_processor import VideoProcessor
from services.speech_analyzer import SpeechAnalyzer
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
            
            # Process frame using existing video processor
            feedback = await self.video_processor.get_realtime_feedback(frame)
            return feedback
            
        except Exception as e:
            return {"error": str(e)}
            
    async def process_audio(self, audio_data: bytes, session_id: str):
        try:
            # Process audio chunk using existing speech analyzer
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