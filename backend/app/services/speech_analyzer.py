import assemblyai as aai
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SpeechMetrics(BaseModel):
    words_per_minute: float = 0.0
    filler_word_count: int = 0
    clarity_score: float = 0.0
    confidence_scores: List[float] = []
    confidence: float = 0.0
    low_confidence_segments: List[Dict[str, Any]] = []  # Added for tracking problematic segments
    segment_confidences: List[Dict[str, Any]] = []  # Added for sentence-level confidence
    overall_quality_score: float = 0.0  # Added composite score
    words: List[str] = []
    raw_transcript: str = ""
    
class SpeechAnalyzer:
    def __init__(self):
        api_key = os.getenv('ASSEMBLY_AI_API_KEY')
        if not api_key:
            raise ValueError("ASSEMBLY_AI_API_KEY not found in environment variables")
            
        # Set the API key globally for the aai client
        aai.settings.api_key = api_key
        
        # Single-word fillers
        self.single_word_fillers = {
            "um", "umm", "uh", "uhh", "ah", "ahh", "er", "erm", 
            "like", "basically", "literally", "actually", "anyway",
            "well", "so", "just", "maybe", "whatever", "yeah"
        }
        
        # Multi-word fillers (as tuples to maintain word order)
        self.multi_word_fillers = [
            ("you", "know"),
            ("you", "know", "what", "i", "mean"),
            ("i", "mean"),
            ("sort", "of"),
            ("kind", "of"),
            ("you", "see"),
            ("pretty", "much")
        ]
    
    def clean_word(self, word: str) -> str:
        """Remove punctuation and convert to lowercase"""
        return ''.join(c for c in word.lower() if c.isalnum() or c.isspace())
    
    def find_filler_phrases(self, words: List[str]) -> List[Dict[str, Any]]:
        """Find both single-word and multi-word filler phrases in the text"""
        filler_words = []
        i = 0
        while i < len(words):
            # Clean the current word
            clean_word = self.clean_word(words[i])
            
            # Check for single-word fillers
            if clean_word in self.single_word_fillers:
                filler_words.append({
                    "word": words[i],
                    "timestamp": i,
                    "type": "single"
                })
                i += 1
                continue
            
            # Check for multi-word fillers
            for filler_phrase in self.multi_word_fillers:
                if i + len(filler_phrase) <= len(words):
                    # Get the sequence of words and clean them
                    sequence = [self.clean_word(words[j]) for j in range(i, i + len(filler_phrase))]
                    if tuple(sequence) == filler_phrase:
                        filler_words.append({
                            "word": " ".join(words[i:i + len(filler_phrase)]),
                            "timestamp": i,
                            "type": "multi"
                        })
                        i += len(filler_phrase)
                        break
            else:
                i += 1
        
        return filler_words

    async def analyze_speech(self, audio_file) -> SpeechMetrics:
        """
        Analyze speech patterns, confidence, and metrics
        """
        try:
            # Get the transcript with detailed analysis
            config = aai.TranscriptionConfig(
                speaker_labels=True,
                word_boost=[
                    "um", "umm", "uh", "uhh", "ah", "ahh", "er", "erm",  # Non-lexical fillers
                    *self.single_word_fillers  # Regular filler words
                ],
                content_safety=True,
                speech_threshold=0.05,
                format_text=False,
                disfluencies=True
            )
            
            # Create transcriber and transcribe the file
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(
                audio_file,
                config=config
            )
            
            words = [word.text for word in transcript.words]
            
            # Find filler words and phrases
            filler_words = self.find_filler_phrases(words)
            
            # Calculate words per minute
            duration_minutes = transcript.audio_duration / 60
            word_count = len(transcript.words)
            wpm = word_count / duration_minutes if duration_minutes > 0 else 0

            # Extract detailed confidence metrics
            confidence_scores = [word.confidence for word in transcript.words]
            word_durations = [word.end - word.start for word in transcript.words]
            total_duration = sum(word_durations)

            # Track low confidence segments (words below 0.4 confidence)
            low_confidence_segments = [
                {
                    "word": word.text,
                    "confidence": word.confidence,
                    "timestamp": word.start,
                    "duration": word.end - word.start
                }
                for word in transcript.words
                if word.confidence < 0.4
            ]

            # Calculate segment-level confidence (by sentences or phrases)
            segments = transcript.utterances if hasattr(transcript, 'utterances') else [transcript]
            segment_confidences = [
                {
                    "text": seg.text,
                    "confidence": sum(w.confidence for w in seg.words) / len(seg.words) if seg.words else 0,
                    "start_time": seg.start,
                    "end_time": seg.end
                }
                for seg in segments
            ]

            # Calculate weighted average confidence based on word duration
            weighted_confidence = sum(
                score * duration / total_duration
                for score, duration in zip(confidence_scores, word_durations)
            ) if total_duration > 0 else 0

            # Calculate overall quality score (composite metric)
            clarity_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            filler_word_ratio = len(filler_words) / len(words) if words else 1
            overall_quality = (
                weighted_confidence * 0.4 +  # Weight for transcription confidence
                clarity_score * 0.4 +        # Weight for pronunciation clarity
                (1 - filler_word_ratio) * 0.2  # Weight for speech fluency
            )

            return SpeechMetrics(
                words_per_minute=wpm,
                filler_word_count=len(filler_words),
                clarity_score=clarity_score,
                confidence_scores=confidence_scores,
                confidence=weighted_confidence,
                low_confidence_segments=low_confidence_segments,
                segment_confidences=segment_confidences,
                overall_quality_score=overall_quality,
                filler_words=filler_words,
                raw_transcript=transcript.text,
                words=words
            )

        except Exception as e:
            raise Exception(f"Speech analysis failed: {str(e)}")
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze the emotional tone and sentiment of the speech
        """
        try:
            # Extended word lists for better sentiment detection
            positive_words = {
                'good', 'great', 'excellent', 'happy', 'confident', 'positive', 'amazing', 
                'wonderful', 'love', 'best', 'excited', 'opportunity', 'perfect', 'success', 
                'successful', 'outstanding', 'fantastic', 'brilliant', 'impressive'
            }
            negative_words = {
                'bad', 'poor', 'terrible', 'unhappy', 'negative', 'hate', 'worst', 'difficult',
                'hard', 'awful', 'worried', 'mistake', 'mistakes', 'fail', 'failed', 'wrong',
                'concern', 'concerned', 'disappointing', 'disappointed', 'nervous', 'anxiety',
                'anxious', 'fear', 'scared'
            }
            neutral_words = {
                'okay', 'ok', 'fine', 'normal', 'average', 'regular', 'standard', 'usual',
                'typical', 'moderate', 'fair', 'nothing special'
            }
            
            text_lower = text.lower()
            words = text_lower.split()
            
            # Check for neutral phrases first
            if any(phrase in text_lower for phrase in neutral_words):
                return {
                    "text": text,
                    "overall_sentiment": "NEUTRAL",
                    "confidence": 0.5
                }
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            if positive_count > negative_count:
                sentiment = "POSITIVE"
                confidence = positive_count / len(words)
            elif negative_count > positive_count:
                sentiment = "NEGATIVE"
                confidence = negative_count / len(words)
            else:
                sentiment = "NEUTRAL"
                confidence = 0.3  # Base confidence for neutral sentiment
            
            return {
                "text": text,
                "overall_sentiment": sentiment,
                "confidence": min(confidence, 1.0)  # Cap confidence at 1.0
            }
        except Exception as e:
            raise Exception(f"Sentiment analysis failed: {str(e)}")

    async def get_realtime_feedback(self, audio_chunk) -> Dict:
        """
        Process audio chunks in real-time for immediate feedback
        """
        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(
                audio_chunk,
                config=aai.TranscriptionConfig(
                    word_boost=list(self.filler_words),
                    speech_threshold=0.2
                )
            )
            
            return {
                "text": transcript.text,
                "is_filler_word": any(word in transcript.text.lower() for word in self.filler_words),
                "confidence": transcript.confidence if hasattr(transcript, 'confidence') else None
            }
            
        except Exception as e:
            raise Exception(f"Real-time analysis failed: {str(e)}")