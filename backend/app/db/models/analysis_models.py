from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class SpeechAnalysisResult(BaseModel):
    words_per_minute: float = 0.0
    filler_word_count: int = 0
    speech_intelligibility: float = 0.0
    pronunciation_accuracy: float = 0.0
    confidence: float = 0.0
    filler_words: List[Dict] = Field(default_factory=list)
    transcript: str = ""
    sentiment: str = "neutral"

class VisualAnalysisResult(BaseModel):
    attention_score: float = 0.0
    eye_contact_percentage: float = 0.0
    posture_score: float = 0.0
    expression_changes: int = 0
    dominant_sentiment: str = "neutral"
    sentiment_timeline: List[Dict] = Field(default_factory=list)

class InterviewAnalysis(BaseModel):
    recording_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: float = 0.0
    speech_analysis: SpeechAnalysisResult = Field(default_factory=SpeechAnalysisResult)
    visual_analysis: VisualAnalysisResult = Field(default_factory=VisualAnalysisResult)
    overall_metrics: Dict = Field(default_factory=dict)
    highlights: List[Dict] = Field(default_factory=list)
    status: str = "pending"

class AnalysisStorage:
    def __init__(self, db):
        self.db = db
        self.collection = db.interview_analyses
        
    async def create_analysis(self, recording_id: str, session_id: str) -> str:
        """Initialize a new analysis document"""
        analysis = InterviewAnalysis(
            recording_id=recording_id,
            session_id=session_id,
            duration=0
        )
        
        result = await self.collection.insert_one(analysis.dict())
        return str(result.inserted_id)
        
    async def update_speech_analysis(self, analysis_id: str, speech_results: SpeechAnalysisResult):
        """Update speech analysis results"""
        await self.collection.update_one(
            {"_id": ObjectId(analysis_id)},
            {"$set": {"speech_analysis": speech_results.dict()}}
        )
        
    async def update_visual_analysis(self, analysis_id: str, visual_results: VisualAnalysisResult):
        """Update visual analysis results"""
        await self.collection.update_one(
            {"_id": ObjectId(analysis_id)},
            {"$set": {"visual_analysis": visual_results.dict()}}
        )
        
    async def finalize_analysis(self, analysis_id: str, overall_metrics: Dict, highlights: List[Dict]):
        """Complete the analysis with overall metrics and highlights"""
        await self.collection.update_one(
            {"_id": ObjectId(analysis_id)},
            {
                "$set": {
                    "overall_metrics": overall_metrics,
                    "highlights": highlights,
                    "status": "completed"
                }
            }
        )
        
    async def get_analysis(self, analysis_id: str) -> Optional[InterviewAnalysis]:
        """Retrieve complete analysis results"""
        doc = await self.collection.find_one({"_id": ObjectId(analysis_id)})
        return InterviewAnalysis(**doc) if doc else None
        
    async def get_session_analyses(self, session_id: str) -> List[InterviewAnalysis]:
        """Get all analyses for a session"""
        analyses = []
        async for doc in self.collection.find({"session_id": session_id}):
            analyses.append(InterviewAnalysis(**doc))
        return analyses