import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import routes with proper paths
from app.api.routes.session_routes import router as session_router
from app.api.routes.auth_routes import router as auth_router
from app.api.routes.analysis_routes import router as analysis_router

app = FastAPI(
    title="Intreview API",
    description="Backend API for the Intreview application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent / "app" / "static"
print(f"Static directory path: {static_dir}")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(session_router, prefix="/api", tags=["sessions"])
app.include_router(analysis_router, prefix="/api", tags=["analysis"])

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