"""
Database model for users collection.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from app.core.constants import AuthProvider


class UserModel(BaseModel):
    """User document model. Uses MongoDB ObjectId as primary identifier."""

    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    name: str
    password_hash: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.LOCAL
    google_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB insertion."""
        data = self.model_dump(exclude={"id"})
        data['auth_provider'] = self.auth_provider.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserModel":
        """Create model from MongoDB document."""
        if '_id' in data:
            data['_id'] = str(data['_id'])
        return cls(**data)

    def get_user_id(self) -> str:
        """Get user ID as string."""
        return self.id
