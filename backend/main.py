import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.routes import session_routes

app = FastAPI(
    title="Intreview API",
    description="Backend API for the Intreview application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent / "app" / "static"
print(f"Static directory path: {static_dir}")  # Add this line to debug
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(session_routes.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Intreview API",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)