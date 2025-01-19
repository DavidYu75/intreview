from fastapi import APIRouter, UploadFile, File
from ..services.speech_analyzer import SpeechAnalyzer

router = APIRouter()
analyzer = SpeechAnalyzer()

@router.post("/analyze")
async def analyze_interview(audio: UploadFile = File(...)):
    # Save temp file
    temp_path = f"temp_{audio.filename}"
    with open(temp_path, "wb") as buffer:
        content = await audio.read()
        buffer.write(content)
    
    try:
        # Analyze the audio
        results = await analyzer.analyze_speech(temp_path)
        return results
    finally:
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
