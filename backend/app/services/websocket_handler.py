from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


    def __init__(self):
        self.active_sessions: Dict[str, WebSocket] = {}
        self.video_processor = VideoProcessor()
        

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


    
    try:
        while True:
            data = await websocket.receive_json()
            response = {"session_id": session_id}
            
            if data["type"] == "video":

            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
