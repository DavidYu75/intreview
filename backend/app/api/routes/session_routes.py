from fastapi import APIRouter, WebSocket, HTTPException, Depends
from typing import Dict, List
import uuid
from datetime import datetime
from bson import ObjectId

from app.services.websocket_handler import handle_websocket
from app.services.recording_storage import RecordingStorage
from app.db.models.analysis_models import AnalysisStorage
from app.services.auth_service import AuthService
from app.db.models.user_models import User
from app.core.config import get_settings

settings = get_settings()

router = APIRouter()

# Initialize services
recording_storage = RecordingStorage(settings.MONGODB_URL, settings.DATABASE_NAME)
analysis_storage = AnalysisStorage(recording_storage.db)
auth_service = AuthService(recording_storage.db)

# In-memory storage for active sessions
active_sessions: Dict[str, Dict] = {}

@router.post("/sessions/start")
async def start_session(current_user: User = Depends(auth_service.get_current_user)):
    """Start a new interview session"""
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "user_id": current_user.id,
        "start_time": datetime.utcnow(),
        "status": "active"
    }
    active_sessions[session_id] = session_data
    
    # Create record in database
    await recording_storage.db.recordings.insert_one({
        "session_id": session_id,
        "user_id": current_user.id,
        "start_time": datetime.utcnow(),
        "status": "active"
    })
    
    return {"session_id": session_id}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time interview processing"""
    if session_id not in active_sessions:
        await websocket.close(code=4004, reason="Invalid session ID")
        return
        
    await handle_websocket(websocket, session_id)

@router.get("/sessions/{session_id}/analysis")
async def get_session_analysis(
    session_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get analysis results for a specific session"""
    try:
        # Check if session belongs to user
        session = await recording_storage.db.recordings.find_one({
            "session_id": session_id,
            "user_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or access denied"
            )
        
        # Get all analyses for the session
        analyses = await analysis_storage.get_session_analyses(session_id)
        
        if not analyses:
            raise HTTPException(
                status_code=404,
                detail="No analysis found for this session"
            )
        
        # Return the most recent analysis
        latest_analysis = max(analyses, key=lambda x: x.timestamp)
        
        return {
            "session_id": session_id,
            "analysis": latest_analysis.dict(),
            "timestamp": latest_analysis.timestamp
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analysis: {str(e)}"
        )

@router.get("/sessions/{session_id}/recording")
async def get_session_recording(
    session_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get recording data for a specific session"""
    try:
        # Find recording for the session and verify ownership
        recording = await recording_storage.db.recordings.find_one({
            "session_id": session_id,
            "user_id": current_user.id
        })
        
        if not recording:
            raise HTTPException(
                status_code=404,
                detail="Recording not found or access denied"
            )
            
        recording_id = str(recording["_id"])
        
        # Get chunks for preview/playback
        video_chunks = await recording_storage.get_recording_chunks(recording_id, "video")
        
        # Return every 10th frame for preview
        preview_frames = video_chunks[::10]
        
        return {
            "session_id": session_id,
            "recording_id": recording_id,
            "duration": recording.get("duration", 0),
            "start_time": recording.get("start_time"),
            "end_time": recording.get("end_time"),
            "frame_count": len(video_chunks),
            "preview_frames": preview_frames[:10]  # First 10 sampled frames
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recording: {str(e)}"
        )

@router.get("/sessions/history")
async def get_session_history(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get session history for current user"""
    try:
        # Get all sessions for the user
        sessions = await recording_storage.db.recordings.find({
            "user_id": current_user.id
        }).sort("start_time", -1).skip(skip).limit(limit).to_list(length=limit)
        
        if not sessions:
            return {
                "sessions": [],
                "total": 0,
                "page": 1,
                "pages": 0
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
            "user_id": current_user.id
        })
        
        return {
            "sessions": session_data,
            "total": total_sessions,
            "page": skip // limit + 1,
            "pages": (total_sessions + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session history: {str(e)}"
        )

@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """End an interview session"""
    # Check if session exists and belongs to user
    session = await recording_storage.db.recordings.find_one({
        "session_id": session_id,
        "user_id": current_user.id
    })
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or access denied"
        )
    
    # Update session status
    await recording_storage.db.recordings.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "completed",
                "end_time": datetime.utcnow()
            }
        }
    )
    
    # Update in-memory session data
    if session_id in active_sessions:
        active_sessions[session_id]["status"] = "completed"
        active_sessions[session_id]["end_time"] = datetime.utcnow()
    
    return {"message": "Session ended successfully"}