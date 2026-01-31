"""
Unit tests for authentication utilities.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from jose import jwt
from bson import ObjectId

from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_google_token,
    get_current_user,
    get_optional_user
)
from app.core.constants import AuthProvider
from app.models.user import UserModel


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_get_password_hash_returns_hash(self):
        """Test that get_password_hash returns a bcrypt hash."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_password_correct(self):
        """Test verify_password with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password with incorrect password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")

        assert hash1 != hash2


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_with_custom_expiry(self):
        """Test access token creation with custom expiry."""
        user_id = "507f1f77bcf86cd799439011"
        expires = timedelta(hours=1)
        token = create_access_token(user_id, expires_delta=expires)

        assert token is not None

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "507f1f77bcf86cd799439011"
        token = create_refresh_token(user_id)

        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        payload = decode_token("invalid-token")
        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        user_id = "507f1f77bcf86cd799439011"
        expires = timedelta(seconds=-1)  # Already expired
        token = create_access_token(user_id, expires_delta=expires)
        payload = decode_token(token)

        assert payload is None

    def test_access_token_contains_access_type(self):
        """Test that access token contains type=access."""
        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert payload["type"] == "access"

    def test_refresh_token_contains_refresh_type(self):
        """Test that refresh token contains type=refresh."""
        user_id = "507f1f77bcf86cd799439011"
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload["type"] == "refresh"


class TestGoogleTokenVerification:
    """Tests for Google OAuth token verification."""

    @pytest.mark.asyncio
    async def test_verify_google_token_valid(self):
        """Test Google token verification with valid token."""
        mock_idinfo = {
            "sub": "google-user-id",
            "email": "test@example.com",
            "name": "Test User"
        }

        with patch("app.core.auth.id_token.verify_oauth2_token", return_value=mock_idinfo):
            result = await verify_google_token("valid-google-token")

            assert result is not None
            assert result["google_id"] == "google-user-id"
            assert result["email"] == "test@example.com"
            assert result["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_verify_google_token_without_name(self):
        """Test Google token verification when name is not provided."""
        mock_idinfo = {
            "sub": "google-user-id",
            "email": "test@example.com"
            # name is missing
        }

        with patch("app.core.auth.id_token.verify_oauth2_token", return_value=mock_idinfo):
            result = await verify_google_token("valid-google-token")

            assert result is not None
            assert result["name"] == "test"  # Should use email prefix

    @pytest.mark.asyncio
    async def test_verify_google_token_invalid(self):
        """Test Google token verification with invalid token."""
        with patch("app.core.auth.id_token.verify_oauth2_token", side_effect=Exception("Invalid token")):
            result = await verify_google_token("invalid-google-token")
            assert result is None


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with valid access token."""
        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(user_id)

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@example.com",
            "name": "Test User",
            "auth_provider": "local",
            "password_hash": "hashed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_user_doc)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch("app.core.auth.get_database", return_value=mock_db):
            user = await get_current_user(mock_credentials)

            assert user is not None
            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        from fastapi import HTTPException

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid-token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_refresh_token_rejected(self):
        """Test get_current_user rejects refresh token."""
        from fastapi import HTTPException

        user_id = "507f1f77bcf86cd799439011"
        token = create_refresh_token(user_id)  # Using refresh token instead of access

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test get_current_user when user doesn't exist."""
        from fastapi import HTTPException

        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(user_id)

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)  # User not found
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch("app.core.auth.get_database", return_value=mock_db):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)

            assert exc_info.value.status_code == 401


class TestGetOptionalUser:
    """Tests for get_optional_user dependency."""

    @pytest.mark.asyncio
    async def test_get_optional_user_no_credentials(self):
        """Test get_optional_user when no credentials provided."""
        result = await get_optional_user(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_invalid_credentials(self):
        """Test get_optional_user with invalid credentials."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid-token"

        result = await get_optional_user(mock_credentials)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_valid_credentials(self):
        """Test get_optional_user with valid credentials."""
        user_id = "507f1f77bcf86cd799439011"
        token = create_access_token(user_id)

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@example.com",
            "name": "Test User",
            "auth_provider": "local",
            "password_hash": "hashed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_user_doc)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch("app.core.auth.get_database", return_value=mock_db):
            user = await get_optional_user(mock_credentials)

            assert user is not None
            assert user.email == "test@example.com"
