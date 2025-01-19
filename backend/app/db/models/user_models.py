from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    email: EmailStr
    name: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "hashed_password": "hashedpass123",
                "is_active": True
            }
        }

class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "name": "John Doe",
                "created_at": "2024-01-19T00:00:00",
                "is_active": True
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"