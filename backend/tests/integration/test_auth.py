"""
Integration tests for authentication endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from bson import ObjectId

from app.main import app
from app.core.auth import get_password_hash, create_access_token, get_current_user, create_refresh_token
from app.core.constants import AuthProvider
from app.models.user import UserModel


@pytest.fixture
def mock_db():
    """Create a mock database."""
    mock_collection = AsyncMock()
    mock_database = MagicMock()
    mock_database.__getitem__ = MagicMock(return_value=mock_collection)
    return mock_database, mock_collection


@pytest.fixture
def auth_test_client(mock_db):
    """Test client with mocked database for testing auth endpoints."""
    mock_database, mock_collection = mock_db

    with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
         patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
         patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

        with TestClient(app) as client:
            yield client, mock_database, mock_collection


class TestRegisterEndpoint:
    """Tests for /auth/register endpoint."""

    def test_register_success(self, mock_db):
        """Test successful user registration."""
        mock_database, mock_collection = mock_db

        mock_collection.find_one = AsyncMock(return_value=None)  # No existing user
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/register", json={
                    "email": "newuser@example.com",
                    "password": "password123",
                    "name": "New User"
                })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_register_email_exists(self, mock_db):
        """Test registration with existing email."""
        mock_database, mock_collection = mock_db

        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "email": "existing@example.com"
        })

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/register", json={
                    "email": "existing@example.com",
                    "password": "password123",
                    "name": "New User"
                })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, mock_db):
        """Test registration with invalid email format."""
        mock_database, mock_collection = mock_db

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/register", json={
                    "email": "invalid-email",
                    "password": "password123",
                    "name": "New User"
                })

        assert response.status_code == 422  # Validation error


class TestLoginEndpoint:
    """Tests for /auth/login endpoint."""

    def test_login_success(self, mock_db):
        """Test successful login."""
        mock_database, mock_collection = mock_db

        password_hash = get_password_hash("password123")
        user_id = ObjectId()
        mock_collection.find_one = AsyncMock(return_value={
            "_id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "password_hash": password_hash,
            "auth_provider": "local",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/login", json={
                    "email": "test@example.com",
                    "password": "password123"
                })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_email(self, mock_db):
        """Test login with non-existent email."""
        mock_database, mock_collection = mock_db

        mock_collection.find_one = AsyncMock(return_value=None)

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/login", json={
                    "email": "nonexistent@example.com",
                    "password": "password123"
                })

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_wrong_password(self, mock_db):
        """Test login with wrong password."""
        mock_database, mock_collection = mock_db

        password_hash = get_password_hash("correctpassword")
        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "email": "test@example.com",
            "name": "Test User",
            "password_hash": password_hash,
            "auth_provider": "local",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/login", json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                })

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_google_user_rejected(self, mock_db):
        """Test login attempt for Google OAuth user."""
        mock_database, mock_collection = mock_db

        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "email": "googleuser@example.com",
            "name": "Google User",
            "password_hash": None,
            "auth_provider": "google",
            "google_id": "google-123",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/login", json={
                    "email": "googleuser@example.com",
                    "password": "anypassword"
                })

        assert response.status_code == 400
        assert "Google sign-in" in response.json()["detail"]


class TestGoogleAuthEndpoint:
    """Tests for /auth/google endpoint."""

    def test_google_auth_new_user(self, mock_db):
        """Test Google auth for new user."""
        mock_database, mock_collection = mock_db

        mock_collection.find_one = AsyncMock(return_value=None)  # No existing user
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database), \
             patch("app.api.v1.endpoints.auth.verify_google_token", new_callable=AsyncMock) as mock_verify:

            mock_verify.return_value = {
                "google_id": "google-123",
                "email": "newgoogle@example.com",
                "name": "Google User"
            }

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/google", json={
                    "credential": "valid-google-token"
                })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_google_auth_existing_user(self, mock_db):
        """Test Google auth for existing user."""
        mock_database, mock_collection = mock_db

        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "email": "existing@example.com",
            "name": "Existing User",
            "google_id": "google-123",
            "auth_provider": "google",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database), \
             patch("app.api.v1.endpoints.auth.verify_google_token", new_callable=AsyncMock) as mock_verify:

            mock_verify.return_value = {
                "google_id": "google-123",
                "email": "existing@example.com",
                "name": "Existing User"
            }

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/google", json={
                    "credential": "valid-google-token"
                })

        assert response.status_code == 200

    def test_google_auth_link_existing_local_user(self, mock_db):
        """Test Google auth linking to existing local user."""
        mock_database, mock_collection = mock_db

        # Existing local user without google_id
        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "email": "local@example.com",
            "name": "Local User",
            "password_hash": "hashed",
            "auth_provider": "local",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database), \
             patch("app.api.v1.endpoints.auth.verify_google_token", new_callable=AsyncMock) as mock_verify:

            mock_verify.return_value = {
                "google_id": "google-new",
                "email": "local@example.com",
                "name": "Local User"
            }

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/google", json={
                    "credential": "valid-google-token"
                })

        assert response.status_code == 200
        mock_collection.update_one.assert_called_once()

    def test_google_auth_invalid_token(self, mock_db):
        """Test Google auth with invalid token."""
        mock_database, mock_collection = mock_db

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database), \
             patch("app.api.v1.endpoints.auth.verify_google_token", new_callable=AsyncMock) as mock_verify:

            mock_verify.return_value = None  # Invalid token

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/google", json={
                    "credential": "invalid-google-token"
                })

        assert response.status_code == 401
        assert "Invalid Google credential" in response.json()["detail"]


class TestRefreshTokenEndpoint:
    """Tests for /auth/refresh endpoint."""

    def test_refresh_token_success(self, mock_db):
        """Test successful token refresh."""
        mock_database, mock_collection = mock_db

        user_id = str(ObjectId())
        refresh_token = create_refresh_token(user_id)

        mock_collection.find_one = AsyncMock(return_value={
            "_id": ObjectId(user_id),
            "email": "test@example.com",
            "name": "Test User",
            "auth_provider": "local",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/refresh", json={
                    "refresh_token": refresh_token
                })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_rejected(self, mock_db):
        """Test refresh endpoint rejects access token."""
        mock_database, mock_collection = mock_db

        user_id = str(ObjectId())
        access_token = create_access_token(user_id)

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/refresh", json={
                    "refresh_token": access_token
                })

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_refresh_with_invalid_token(self, mock_db):
        """Test refresh endpoint with invalid token."""
        mock_database, mock_collection = mock_db

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/refresh", json={
                    "refresh_token": "invalid-token"
                })

        assert response.status_code == 401

    def test_refresh_user_not_found(self, mock_db):
        """Test refresh when user no longer exists."""
        mock_database, mock_collection = mock_db

        user_id = str(ObjectId())
        refresh_token = create_refresh_token(user_id)

        mock_collection.find_one = AsyncMock(return_value=None)

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.auth.get_database', return_value=mock_database):

            with TestClient(app) as client:
                response = client.post("/api/v1/auth/refresh", json={
                    "refresh_token": refresh_token
                })

        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]


class TestGetMeEndpoint:
    """Tests for /auth/me endpoint."""

    def test_get_me_success(self):
        """Test getting current user profile."""
        mock_user = UserModel(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            name="Test User",
            auth_provider=AuthProvider.LOCAL,
            password_hash="hashed"
        )

        async def mock_get_current_user():
            return mock_user

        mock_db = MagicMock()

        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock):

            app.dependency_overrides[get_current_user] = mock_get_current_user

            with TestClient(app) as client:
                response = client.get("/api/v1/auth/me")

            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_get_me_unauthorized(self):
        """Test getting current user without authentication."""
        with patch('app.main.connect_to_mongo', new_callable=AsyncMock), \
             patch('app.main.close_mongo_connection', new_callable=AsyncMock):

            # Clear any existing overrides
            app.dependency_overrides.clear()

            with TestClient(app) as client:
                response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No auth header
