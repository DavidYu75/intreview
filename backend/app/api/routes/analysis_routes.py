from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.speech_analyzer import SpeechAnalyzer
import os

router = APIRouter()

analyzer = SpeechAnalyzer()

@router.post("/analyze")
async def analyze_interview(audio: UploadFile = File(...)):
    """Analyze uploaded audio file - No auth required"""
    try:
        # Create a unique temp filename
        temp_path = f"temp_{audio.filename}"
        
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
        try:
            # Analyze the audio
            results = await analyzer.analyze_speech(temp_path)
            return results
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing audio: {str(e)}"
        )