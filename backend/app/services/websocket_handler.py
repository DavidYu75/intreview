from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime

from app.services.video_processor import VideoProcessor
import cv2
import numpy as np
import base64

class VideoAnalysisManager:
    def __init__(self):
        self.video_processor = VideoProcessor()

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

# Create a global manager
analysis_manager = VideoAnalysisManager()

async def handle_websocket(websocket: WebSocket):
    """Main WebSocket handler - No session management"""
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