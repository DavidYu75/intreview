import assemblyai as aai
from ..core.config import get_settings

settings = get_settings()

class SpeechAnalyzer:
    def __init__(self):
        self.client = aai.Client(api_key=settings.ASSEMBLY_AI_API_KEY)
    
    async def analyze_speech(self, audio_file):
        """
        Analyze speech patterns, confidence, and metrics
        """
        # Add speech analysis logic here
        pass
    
    async def transcribe_audio(self, audio_file):
        """
        Transcribe audio to text
        """
        try:
            transcript = await self.client.transcribe(audio_file)
            return transcript.text
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")