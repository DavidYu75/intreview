from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.video_processor import VideoProcessor
from app.services.recording_storage import RecordingStorage
from app.services.post_processor import PostProcessor
from app.db.models.analysis_models import AnalysisStorage
from app.core.config import get_settings

settings = get_settings()
class InterviewSessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, WebSocket] = {}
        self.video_processor = VideoProcessor()
        self.recording_storage = RecordingStorage(
            settings.MONGODB_URL,
            settings.DATABASE_NAME
        )
        self.analysis_storage = AnalysisStorage(self.recording_storage.db)
        self.post_processor = PostProcessor(
            self.recording_storage,
            self.analysis_storage
        )
        
        # Track recording IDs for each session
        self.session_recordings: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Initialize session and start recording"""
        await websocket.accept()
        self.active_sessions[session_id] = websocket
        
        # Start new recording
        recording_id = await self.recording_storage.start_recording(session_id)
        self.session_recordings[session_id] = recording_id
        
        # Send confirmation to client
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id,
            "recording_id": recording_id
        })
        
    async def disconnect(self, session_id: str):
        """Clean up session and trigger post-processing"""
        if session_id in self.active_sessions:
            # End recording if exists
            if session_id in self.session_recordings:
                recording_id = self.session_recordings[session_id]
                try:
                    # End recording
                    await self.recording_storage.end_recording(recording_id)
                    
                    # Start post-processing
                    analysis_id = await self.post_processor.process_recording(
                        recording_id,
                        session_id
                    )
                    
                    # Send final analysis to client if still connected
                    websocket = self.active_sessions.get(session_id)
                    if websocket:
                        analysis = await self.analysis_storage.get_analysis(analysis_id)
                        if analysis:
                            await websocket.send_json({
                                "type": "analysis_complete",
                                "analysis_id": analysis_id,
                                "results": analysis.dict()
                            })
                            
                except Exception as e:
                    print(f"Error during session cleanup: {e}")
                    
                del self.session_recordings[session_id]
                
            del self.active_sessions[session_id]
            
    async def process_frame(self, frame_data: str, session_id: str):
        """Process and store video frame"""
        try:
            # Store frame in recording
            if session_id in self.session_recordings:
                recording_id = self.session_recordings[session_id]
                await self.recording_storage.store_chunk(
                    recording_id,
                    frame_data,
                    "video",
                    datetime.utcnow()
                )
            
            # Process frame for real-time feedback
            encoded_data = frame_data.split(',')[1] if ',' in frame_data else frame_data
            import base64
            import numpy as np
            import cv2
            
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
            
    async def process_audio(self, audio_data: str, session_id: str):
        """Store audio chunk"""
        try:
            if session_id in self.session_recordings:
                recording_id = self.session_recordings[session_id]
                await self.recording_storage.store_chunk(
                    recording_id,
                    audio_data,
                    "audio",
                    datetime.utcnow()
                )
            return {"status": "success"}
        except Exception as e:
            print(f"Error processing audio: {e}")
            return {"status": "error"}

# Create a global session manager
session_manager = InterviewSessionManager()

async def handle_websocket(websocket: WebSocket, session_id: str):
    """Main WebSocket handler"""
    await session_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive and process messages
            data = await websocket.receive_json()
            response = {"session_id": session_id}
            
            if data["type"] == "video":
                feedback = await session_manager.process_frame(
                    data["frame"],
                    session_id
                )
                response["type"] = "video_feedback"
                response["feedback"] = feedback
                
            elif data["type"] == "audio":
                result = await session_manager.process_audio(
                    data["audio"],
                    session_id
                )
                response["type"] = "audio_received"
                response["status"] = result["status"]
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        await session_manager.disconnect(session_id)
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
        await session_manager.disconnect(session_id)