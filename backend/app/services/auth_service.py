from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.db.models.user_models import UserInDB, User, Token

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    async def get_user(self, email: str) -> Optional[UserInDB]:
        user_dict = await self.users.find_one({"email": email})
        if user_dict:
            # Convert _id to string id
            user_dict['id'] = str(user_dict.pop('_id'))
            return UserInDB(**user_dict)
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return User(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            is_active=user.is_active
        )

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )

    async def create_user(self, email: str, password: str, name: str) -> User:
        # Check if user already exists
        existing_user = await self.get_user(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Create new user document
        user_doc = {
            "_id": ObjectId(),  # MongoDB document ID
            "email": email,
            "name": name,
            "hashed_password": self.get_password_hash(password),
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Insert into database
        await self.users.insert_one(user_doc)
        
        # Return user model (without password)
        return User(
            id=str(user_doc["_id"]),
            email=user_doc["email"],
            name=user_doc["name"],
            created_at=user_doc["created_at"],
            is_active=user_doc["is_active"]
        )

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await self.get_user(email)
        if user is None:
            raise credentials_exception
            
        return User(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
            is_active=user.is_active
        )