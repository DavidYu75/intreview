import assemblyai as aai
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import math
from datetime import datetime

# Load environment variables
load_dotenv()

class SpeechMetrics(BaseModel):
    words_per_minute: float = 0.0
    filler_word_count: int = 0
    speech_intelligibility: float = 0.0  # Renamed from clarity_score
    pronunciation_accuracy: float = 0.0  # Placeholder for phoneme-based scoring
    articulation_enunciation: float = 0.0  # Placeholder for articulation analysis
    silent_pause_ratio: float = 0.0  # Placeholder for silent pause ratio
    speech_intelligibility_score: float = 0.0  # New integrated metric
    confidence_scores: List[float] = []
    confidence: float = 0.0
    low_confidence_segments: List[Dict[str, Any]] = []  # Added for tracking problematic segments
    segment_confidences: List[Dict[str, Any]] = []  # Added for sentence-level confidence
    filler_words: List[Dict[str, Any]] = []  # Added missing attribute
    words: List[str] = []
    raw_transcript: str = ""
    duration_minutes: float = 0.0
    interview_date: str = ""

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

    def calculate_weighted_confidence(self, confidence_scores: List[float], word_durations: List[float]) -> float:
        """
        Calculate weighted confidence based on:
        - Word duration (longer words have more impact)
        - Confidence thresholds:
          * Words below 60% confidence get extra penalty
          * Penalty is dampened by 50% to avoid over-penalization
        - Returns weighted average considering word importance by duration
        """
        total_duration = sum(word_durations)
        if (total_duration == 0):
            return 1.0  # Perfect confidence if no words

        weighted_sum = 0
        total_weight = 0

        for confidence, duration in zip(confidence_scores, word_durations):
            weight = duration / total_duration
            if confidence < 0.6:  # Low confidence threshold
                penalty = 1 - confidence  # Penalize based on how low the confidence is
                dampened_penalty = penalty * 0.5  # Dampening factor for small mistakes
                weighted_sum += (confidence - dampened_penalty) * weight
            else:
                weighted_sum += confidence * weight
            total_weight += weight

        return weighted_sum / total_weight

    def calculate_speech_intelligibility(self, confidence_scores: List[float], filler_word_ratio: float) -> float:
        """
        Calculate speech intelligibility score based on:
        - Base confidence from word-level accuracy
        - Filler word penalties:
          * Light penalty (0.5x) for filler ratio under 15%
          * Heavy penalty (squared) for filler ratio over 15%
        - Maintains minimum score of 50% to avoid discouragement
        """
        base_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 1.0

        # Penalize filler word ratio non-linearly
        if filler_word_ratio > 0.15:  # Threshold for "excessive"
            filler_penalty = filler_word_ratio ** 2  # Quadratic penalty
        else:
            filler_penalty = filler_word_ratio * 0.5  # Reduced penalty for minor filler usage

        # Final intelligibility score
        return max(base_score - filler_penalty, 0.5)  # Ensure a floor to prevent overly discouraging scores

    def calculate_filler_word_score(self, filler_count: int, duration_minutes: float) -> float:
        """
        Calculate a score for filler word usage (0 to 1, where 1 is best)
        Baseline expectations:
        - Excellent: ≤ 1 filler per minute
        - Good: ≤ 2 fillers per minute
        - Fair: ≤ 4 fillers per minute
        - Poor: > 4 fillers per minute
        """
        if duration_minutes == 0:
            return 1.0

        fillers_per_minute = filler_count / duration_minutes
        
        if fillers_per_minute <= 1:
            return 1.0
        elif fillers_per_minute <= 2:
            return 0.8
        elif fillers_per_minute <= 4:
            return 0.6
        else:
            # Exponential decay for worse performances
            return max(0.2, math.exp(-fillers_per_minute/10))

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
            transcript = transcriber.transcribe(audio_file, config=config)

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

            # Identify low confidence segments
            low_confidence_segments = [
                {
                    "word": word.text,
                    "confidence": word.confidence,
                    "timestamp": word.start,
                    "duration": word.end - word.start
                }
                for word in transcript.words if word.confidence < 0.4
            ]

            # Calculate metrics
            weighted_confidence = self.calculate_weighted_confidence(confidence_scores, word_durations)
            filler_word_ratio = len(filler_words) / len(words) if words else 0
            filler_word_score = self.calculate_filler_word_score(len(filler_words), duration_minutes)
            
            # Updated speech intelligibility calculation with proper weighting
            speech_intelligibility = (
                weighted_confidence * 0.6 +  # Base confidence has higher weight
                filler_word_score * 0.4      # Filler word score has lower weight
            )

            # Get current date and time
            interview_date = datetime.now().isoformat()

            return SpeechMetrics(
                words_per_minute=wpm,
                filler_word_count=len(filler_words),
                speech_intelligibility=speech_intelligibility,
                pronunciation_accuracy=0.0,  # Placeholder
                articulation_enunciation=0.0,  # Placeholder
                silent_pause_ratio=0.0,  # Placeholder
                speech_intelligibility_score=speech_intelligibility,
                confidence_scores=confidence_scores,
                confidence=weighted_confidence,
                low_confidence_segments=low_confidence_segments,
                segment_confidences=[],  # Placeholder for future implementation
                filler_words=filler_words,
                raw_transcript=transcript.text,
                words=words,
                duration_minutes=duration_minutes,
                interview_date=interview_date
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
