import numpy as np
import cv2
from typing import List, Dict, Tuple
from datetime import datetime

from app.services.speech_analyzer import SpeechAnalyzer
from app.services.video_processor import VideoProcessor
from app.db.models.analysis_models import (
    SpeechAnalysisResult,
    VisualAnalysisResult,
    InterviewAnalysis
)

class PostProcessor:
    def __init__(self, recording_storage, analysis_storage):
        self.recording_storage = recording_storage
        self.analysis_storage = analysis_storage
        self.speech_analyzer = SpeechAnalyzer()
        self.video_processor = VideoProcessor()
        
    async def process_recording(self, recording_id: str, session_id: str) -> str:
        """Process a complete recording and generate analysis"""
        try:
            # Initialize analysis document
            analysis_id = await self.analysis_storage.create_analysis(recording_id, session_id)
            
            # Get all chunks
            try:
                video_chunks = await self.recording_storage.get_recording_chunks(recording_id, "video")
                audio_chunks = await self.recording_storage.get_recording_chunks(recording_id, "audio")
            except Exception as e:
                print(f"Error getting chunks: {e}")
                video_chunks = []
                audio_chunks = []
            
            # Initialize default results
            speech_results = SpeechAnalysisResult()
            visual_results = VisualAnalysisResult()
            
            # Process video if available
            if video_chunks:
                try:
                    visual_results = await self._analyze_visual(video_chunks)
                except Exception as e:
                    print(f"Visual analysis error: {e}")
            
            # Process audio if available
            if audio_chunks:
                try:
                    speech_results = await self._analyze_speech(audio_chunks)
                except Exception as e:
                    print(f"Speech analysis error: {e}")
            
            # Generate overall metrics and highlights
            overall_metrics, highlights = self._generate_overall_analysis(
                speech_results,
                visual_results
            )
            
            # Update analysis document
            try:
                await self.analysis_storage.update_speech_analysis(analysis_id, speech_results)
                await self.analysis_storage.update_visual_analysis(analysis_id, visual_results)
                await self.analysis_storage.finalize_analysis(
                    analysis_id,
                    overall_metrics,
                    highlights
                )
            except Exception as e:
                print(f"Error updating analysis: {e}")
            
            return analysis_id
            
        except Exception as e:
            print(f"Post-processing failed: {e}")
            raise

    async def _analyze_speech(self, audio_chunks: List[Dict]) -> SpeechAnalysisResult:
        """Analyze speech from audio chunks"""
        if not audio_chunks:
            return SpeechAnalysisResult()
            
        try:
            # Create empty audio for testing since we don't have real audio processing yet
            combined_audio = b""  # This would normally be processed audio
            
            return SpeechAnalysisResult(
                words_per_minute=120.0,  # Sample values for testing
                filler_word_count=5,
                speech_intelligibility=0.85,
                pronunciation_accuracy=0.9,
                confidence=0.8,
                transcript="Sample transcript",
                sentiment="neutral"
            )
            
        except Exception as e:
            print(f"Speech analysis failed: {e}")
            return SpeechAnalysisResult()

    async def _analyze_visual(self, video_chunks: List[Dict]) -> VisualAnalysisResult:
        """Analyze visual aspects from video chunks"""
        if not video_chunks:
            return VisualAnalysisResult()
            
        try:
            frames = self._decode_video_chunks(video_chunks)
            
            attention_scores = []
            sentiments = []
            posture_scores = []
            
            for frame in frames:
                feedback = await self.video_processor.get_realtime_feedback(frame)
                
                attention_scores.append(1.0 if feedback["attention_status"] == "centered" else 0.0)
                sentiments.append(feedback["sentiment"])
                
                if feedback.get("face_position"):
                    pos = feedback["face_position"]
                    pos_score = 1.0 - (abs(pos["x"]/320) + abs(pos["y"]/240))/2
                    posture_scores.append(max(0.0, pos_score))
                else:
                    posture_scores.append(0.0)
            
            return VisualAnalysisResult(
                attention_score=np.mean(attention_scores) if attention_scores else 0.0,
                eye_contact_percentage=len([s for s in attention_scores if s > 0.8]) / max(len(attention_scores), 1) * 100,
                posture_score=np.mean(posture_scores) if posture_scores else 0.0,
                expression_changes=sum(1 for i in range(1, len(sentiments)) if sentiments[i] != sentiments[i-1]),
                dominant_sentiment=max(set(sentiments), key=sentiments.count) if sentiments else "neutral",
                sentiment_timeline=self._create_sentiment_timeline(sentiments)
            )
            
        except Exception as e:
            print(f"Visual analysis failed: {e}")
            return VisualAnalysisResult()

    def _decode_video_chunks(self, video_chunks: List[Dict]) -> List[np.ndarray]:
        """Convert base64 encoded video chunks to frames"""
        frames = []
        for chunk in video_chunks:
            try:
                import base64
                base64_data = chunk["data"].split(",")[-1]
                nparr = np.frombuffer(base64.b64decode(base64_data), np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    frames.append(frame)
                    
            except Exception as e:
                print(f"Error decoding frame: {e}")
                continue
                
        return frames

    def _create_sentiment_timeline(self, sentiments: List[str]) -> List[Dict]:
        """Create a timeline of sentiment changes"""
        timeline = []
        if not sentiments:
            return timeline
            
        current_sentiment = sentiments[0]
        start_idx = 0
        
        for i, sentiment in enumerate(sentiments[1:], 1):
            if sentiment != current_sentiment:
                timeline.append({
                    "sentiment": current_sentiment,
                    "start_frame": start_idx,
                    "end_frame": i-1,
                    "duration": i - start_idx
                })
                current_sentiment = sentiment
                start_idx = i
        
        timeline.append({
            "sentiment": current_sentiment,
            "start_frame": start_idx,
            "end_frame": len(sentiments)-1,
            "duration": len(sentiments) - start_idx
        })
        
        return timeline

    def _generate_overall_analysis(
        self,
        speech_results: SpeechAnalysisResult,
        visual_results: VisualAnalysisResult
    ) -> Tuple[Dict, List[Dict]]:
        """Generate overall metrics and highlights"""
        overall_metrics = {
            "overall_confidence": speech_results.confidence,
            "overall_engagement": (visual_results.attention_score + 
                                 visual_results.eye_contact_percentage/100) / 2,
            "communication_score": (
                speech_results.speech_intelligibility * 0.4 +
                (1 - min(speech_results.filler_word_count / 50, 1)) * 0.3 +
                visual_results.posture_score * 0.3
            )
        }
        
        highlights = []
        if speech_results.filler_word_count > 0:
            highlights.append({
                "type": "observation",
                "category": "speech",
                "message": f"Used {speech_results.filler_word_count} filler words"
            })
            
        if visual_results.eye_contact_percentage > 60:
            highlights.append({
                "type": "strength",
                "category": "visual",
                "message": "Good eye contact maintained"
            })
        
        return overall_metrics, highlights