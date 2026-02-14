"""
Tests for authentication endpoints
"""
import pytest
from datetime import datetime


class TestRegistration:
    """Test user registration"""

    def test_register_new_user(self, client):
        """Test successful registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "name": "New User",
                "date_of_birth": "1995-06-15",
                "gender": "male"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user_id" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "user"

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",  # Already exists
                "password": "SecurePass123",
                "name": "Duplicate User",
                "date_of_birth": "1995-06-15",
                "gender": "male"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email_case_insensitive(self, client, test_user):
        """Test duplicate registration check is case-insensitive"""
        response = client.post(
            "/auth/register",
            json={
                "email": "TEST@EXAMPLE.COM",  # Same as fixture email, different case
                "password": "SecurePass123",
                "name": "Duplicate User",
                "date_of_birth": "1995-06-15",
                "gender": "male"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",  # Too short, no uppercase, no digit
                "name": "New User",
                "date_of_birth": "1995-06-15",
                "gender": "male"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_underage(self, client):
        """Test registration with age under 18"""
        today = datetime.now()
        underage_dob = today.replace(year=today.year - 17)

        response = client.post(
            "/auth/register",
            json={
                "email": "underage@example.com",
                "password": "SecurePass123",
                "name": "Underage User",
                "date_of_birth": underage_dob.strftime("%Y-%m-%d"),
                "gender": "male"
            }
        )

        assert response.status_code == 422
        assert "18 years old" in str(response.json())

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post(
            "/auth/register",
            json={
                "email": "notanemail",
                "password": "SecurePass123",
                "name": "Invalid User",
                "date_of_birth": "1995-06-15",
                "gender": "male"
            }
        )

        assert response.status_code == 422


class TestLogin:
    """Test user login"""

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_id"] == test_user.id
        assert data["role"] == "user"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123"
            }
        )

        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123"
            }
        )

        assert response.status_code == 401

    def test_login_admin(self, client, test_admin):
        """Test admin login"""
        response = client.post(
            "/auth/login",
            json={
                "email": "admin@example.com",
                "password": "AdminPass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    def test_login_email_case_insensitive(self, client, test_user):
        """Test login works when email case differs"""
        response = client.post(
            "/auth/login",
            json={
                "email": "TEST@EXAMPLE.COM",
                "password": "TestPass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user.id


class TestTokenValidation:
    """Test token validation"""

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"

    def test_verify_token(self, client, auth_headers):
        """Test token verification"""
        response = client.post("/auth/verify-token", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data

    def test_invalid_token(self, client):
        """Test with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    def test_missing_token(self, client):
        """Test without token"""
        response = client.get("/auth/me")

        assert response.status_code == 401


class TestLogout:
    """Test logout"""

    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post("/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
