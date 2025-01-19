from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .routes import analysis
from .services.websocket_handler import handle_websocket
import uuid

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis.router)

@app.get("/")
async def root():
    return {"message": "Intreview API is running"}

@app.websocket("/api/ws/video")
async def websocket_endpoint(websocket: WebSocket):
    session_id = str(uuid.uuid4())
    await handle_websocket(websocket, session_id)
