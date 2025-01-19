import sys
import os
from fastapi import APIRouter, WebSocket, HTTPException
from typing import Dict
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.websocket_handler import handle_websocket

router = APIRouter()

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

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get details of a specific session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return active_sessions[session_id]

@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str):
    """End an interview session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = active_sessions[session_id]
    session["end_time"] = datetime.utcnow()
    session["status"] = "completed"
    
    return {"message": "Session ended successfully"}