import sys
import os
from fastapi import APIRouter, WebSocket, HTTPException
from typing import Dict, List
import uuid
from datetime import datetime
from bson import ObjectId


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.websocket_handler import handle_websocket
from app.services.recording_storage import RecordingStorage
from app.db.models.analysis_models import AnalysisStorage
from app.core.config import get_settings

settings = get_settings()

router = APIRouter()
# Initialize services
recording_storage = RecordingStorage(settings.MONGODB_URL, settings.DATABASE_NAME)
analysis_storage = AnalysisStorage(recording_storage.db)

# In-memory storage for active sessions
active_sessions: Dict[str, Dict] = {}

@router.post("/sessions/start")
async def start_session():
    """Start a new interview session"""
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "start_time": datetime.utcnow(),
        "status": "active"
    }
    active_sessions[session_id] = session_data
    return {"session_id": session_id}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time interview processing"""
    if session_id not in active_sessions:
        await websocket.close(code=4004, reason="Invalid session ID")
        return
        
    await handle_websocket(websocket, session_id)

@router.get("/sessions/{session_id}/analysis")
async def get_session_analysis(session_id: str):
    """Get analysis results for a specific session"""
    try:
        # Get all analyses for the session
        analyses = await analysis_storage.get_session_analyses(session_id)
        
        if not analyses:
            raise HTTPException(status_code=404, detail="No analysis found for this session")
        
        # Return the most recent analysis
        latest_analysis = max(analyses, key=lambda x: x.timestamp)
        
        return {
            "session_id": session_id,
            "analysis": latest_analysis.dict(),
            "timestamp": latest_analysis.timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")

@router.get("/sessions/{session_id}/recording")
async def get_session_recording(session_id: str):
    """Get recording data for a specific session"""
    try:
        # Find recording ID for the session
        recordings = await recording_storage.db.recordings.find({
            "session_id": session_id
        }).to_list(length=1)
        
        if not recordings:
            raise HTTPException(status_code=404, detail="No recording found for this session")
            
        recording = recordings[0]
        recording_id = str(recording["_id"])
        
        # Get chunks for preview/playback
        video_chunks = await recording_storage.get_recording_chunks(recording_id, "video")
        
        # We'll return a sample of frames for preview
        sample_rate = 10  # Return every 10th frame
        preview_frames = video_chunks[::sample_rate]
        
        return {
            "session_id": session_id,
            "recording_id": recording_id,
            "duration": recording.get("duration", 0),
            "start_time": recording.get("start_time"),
            "end_time": recording.get("end_time"),
            "frame_count": len(video_chunks),
            "preview_frames": preview_frames[:10]  # Limit to first 10 sampled frames
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recording: {str(e)}")

@router.get("/sessions/user/{user_id}/history")
async def get_user_session_history(user_id: str, skip: int = 0, limit: int = 10):
    """Get session history for a specific user"""
    try:
        # Get all sessions for the user
        sessions = await recording_storage.db.recordings.find({
            "user_id": user_id  # Note: You'll need to store user_id in recordings
        }).sort("start_time", -1).skip(skip).limit(limit).to_list(length=limit)
        
        if not sessions:
            return {
                "user_id": user_id,
                "sessions": [],
                "total": 0
            }
        
        # Get analysis results for each session
        session_data = []
        for session in sessions:
            session_id = session["session_id"]
            
            # Get latest analysis for the session
            analyses = await analysis_storage.get_session_analyses(session_id)
            latest_analysis = max(analyses, key=lambda x: x.timestamp) if analyses else None
            
            session_data.append({
                "session_id": session_id,
                "start_time": session["start_time"],
                "end_time": session.get("end_time"),
                "duration": session.get("duration", 0),
                "status": session.get("status", "unknown"),
                "has_analysis": latest_analysis is not None,
                "analysis_summary": {
                    "overall_metrics": latest_analysis.overall_metrics if latest_analysis else None,
                    "timestamp": latest_analysis.timestamp if latest_analysis else None
                } if latest_analysis else None
            })
        
        # Get total count for pagination
        total_sessions = await recording_storage.db.recordings.count_documents({
            "user_id": user_id
        })
        
        return {
            "user_id": user_id,
            "sessions": session_data,
            "total": total_sessions,
            "page": skip // limit + 1,
            "pages": (total_sessions + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session history: {str(e)}")

@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str):
    """End an interview session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    session["end_time"] = datetime.utcnow()
    session["status"] = "completed"
    
    return {"message": "Session ended successfully"}