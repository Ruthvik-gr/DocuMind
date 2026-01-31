"""
Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from bson import ObjectId
import logging

from app.core.database import get_database
from app.core.constants import COLLECTION_USERS, AuthProvider
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_google_token,
    get_current_user
)
from app.models.user import UserModel
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleAuthRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user with email and password."""
    db = get_database()

    existing_user = await db[COLLECTION_USERS].find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = UserModel(
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        auth_provider=AuthProvider.LOCAL,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    result = await db[COLLECTION_USERS].insert_one(user.to_dict())
    user_id = str(result.inserted_id)

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id)
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    db = get_database()

    user_doc = await db[COLLECTION_USERS].find_one({"email": request.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user = UserModel.from_dict(user_doc)

    if user.auth_provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please use Google sign-in for this account"
        )

    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user_id = str(user_doc["_id"])

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id)
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest):
    """Authenticate with Google OAuth."""
    google_user = await verify_google_token(request.credential)

    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential"
        )

    db = get_database()

    user_doc = await db[COLLECTION_USERS].find_one({
        "$or": [
            {"google_id": google_user["google_id"]},
            {"email": google_user["email"]}
        ]
    })

    if user_doc:
        if not user_doc.get("google_id"):
            await db[COLLECTION_USERS].update_one(
                {"_id": user_doc["_id"]},
                {
                    "$set": {
                        "google_id": google_user["google_id"],
                        "auth_provider": AuthProvider.GOOGLE.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        user_id = str(user_doc["_id"])
    else:
        user = UserModel(
            email=google_user["email"],
            name=google_user["name"],
            password_hash=None,
            auth_provider=AuthProvider.GOOGLE,
            google_id=google_user["google_id"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        result = await db[COLLECTION_USERS].insert_one(user.to_dict())
        user_id = str(result.inserted_id)

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    db = get_database()
    user_doc = await db[COLLECTION_USERS].find_one({"_id": ObjectId(user_id)})

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        auth_provider=current_user.auth_provider.value,
        created_at=current_user.created_at
    )
