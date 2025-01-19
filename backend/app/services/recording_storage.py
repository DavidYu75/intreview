from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import base64

class RecordingStorage:
    def __init__(self, mongodb_url: str, database_name: str):
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[database_name]
        self.recordings = self.db.recordings
        self.chunks = self.db.recording_chunks
        
    async def start_recording(self, session_id: str) -> str:
        """Initialize a new recording entry"""
        recording_doc = {
            "session_id": session_id,
            "start_time": datetime.utcnow(),
            "status": "recording",
            "chunks": [],
            "duration": 0
        }
        result = await self.recordings.insert_one(recording_doc)
        return str(result.inserted_id)
        
    async def store_chunk(self, recording_id: str, chunk_data: str, chunk_type: str, timestamp: datetime = None):
        """Store a video/audio chunk"""
        try:
            # Decode base64 data
            binary_data = base64.b64decode(chunk_data.split(',')[1] if ',' in chunk_data else chunk_data)
            
            chunk_doc = {
                "recording_id": ObjectId(recording_id),
                "timestamp": timestamp or datetime.utcnow(),
                "type": chunk_type,
                "data": binary_data
            }
            
            result = await self.chunks.insert_one(chunk_doc)
            
            # Update recording document with chunk reference
            await self.recordings.update_one(
                {"_id": ObjectId(recording_id)},
                {"$push": {"chunks": result.inserted_id}}
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            raise Exception(f"Failed to store chunk: {str(e)}")
            
    async def end_recording(self, recording_id: str):
        """Finalize recording and prepare for post-processing"""
        recording = await self.recordings.find_one({"_id": ObjectId(recording_id)})
        if not recording:
            raise Exception("Recording not found")
            
        end_time = datetime.utcnow()
        duration = (end_time - recording["start_time"]).total_seconds()
        
        await self.recordings.update_one(
            {"_id": ObjectId(recording_id)},
            {
                "$set": {
                    "status": "completed",
                    "end_time": end_time,
                    "duration": duration
                }
            }
        )
        
        return {
            "recording_id": str(recording_id),
            "duration": duration,
            "chunk_count": len(recording["chunks"])
        }
    
    async def get_recording_chunks(self, recording_id: str, chunk_type: str = None):
        """Retrieve all chunks for a recording in order"""
        query = {"recording_id": ObjectId(recording_id)}
        if chunk_type:
            query["type"] = chunk_type
            
        chunks = []
        async for chunk in self.chunks.find(query).sort("timestamp"):
            chunks.append({
                "id": str(chunk["_id"]),
                "type": chunk["type"],
                "data": base64.b64encode(chunk["data"]).decode(),
                "timestamp": chunk["timestamp"]
            })
            
        return chunks
    
    async def delete_recording(self, recording_id: str):
        """Delete a recording and its chunks"""
        # Delete all chunks
        await self.chunks.delete_many({"recording_id": ObjectId(recording_id)})
        # Delete recording document
        await self.recordings.delete_one({"_id": ObjectId(recording_id)})