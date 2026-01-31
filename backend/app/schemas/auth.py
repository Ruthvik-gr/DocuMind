"""
Authentication request/response schemas.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """Google OAuth request."""
    credential: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    name: str
    auth_provider: str
    created_at: datetime
