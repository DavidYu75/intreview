# app/api/routes/analysis_routes.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from ...services.speech_analyzer import SpeechAnalyzer
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analysis",  # This means final routes become "/analysis/..."
    tags=["analysis"]
)

analyzer = SpeechAnalyzer()

@router.post("/speech")  # -> final path is "/analysis/speech"
async def analyze_speech(audio: UploadFile = File(...)):
    """Analyze speech from uploaded audio file"""
    logger.info(f"Received audio file for analysis: {audio.filename}")

    try:
        # Read the audio file content
        audio_content = await audio.read()
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Save to temporary file and analyze
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(audio_content)
            temp_audio.flush()

            logger.info(f"Analyzing speech from temporary file: {temp_audio.name}")
            results = await analyzer.analyze_speech(temp_audio.name)

            if not results:
                raise HTTPException(status_code=500, detail="Speech analysis failed")

            return results

    except Exception as e:
        logger.error(f"Speech analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
