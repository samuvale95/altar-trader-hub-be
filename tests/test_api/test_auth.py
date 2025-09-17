"""
Tests for authentication API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient, test_user_data):
    """Test user registration."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["first_name"] == test_user_data["first_name"]
    assert data["last_name"] == test_user_data["last_name"]
    assert "id" in data
    assert "created_at" in data


def test_register_duplicate_user(client: TestClient, test_user_data):
    """Test registering duplicate user."""
    # Register first user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    
    # Try to register same user again
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_user(client: TestClient, test_user):
    """Test user login."""
    login_data = {
        "email": test_user["email"],
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, test_user):
    """Test login with invalid credentials."""
    login_data = {
        "email": test_user["email"],
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user(client: TestClient, auth_headers):
    """Test getting current user info."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "first_name" in data
    assert "last_name" in data


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without authentication."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_token(client: TestClient, test_user):
    """Test token refresh."""
    # First login to get tokens
    login_data = {
        "email": test_user["email"],
        "password": "testpassword123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    refresh_token = token_data["refresh_token"]
    
    # Refresh token
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    
    new_token_data = response.json()
    assert "access_token" in new_token_data
    assert "refresh_token" in new_token_data


def test_logout_user(client: TestClient, auth_headers):
    """Test user logout."""
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]


def test_register_validation(client: TestClient):
    """Test user registration validation."""
    # Test missing email
    response = client.post("/api/v1/auth/register", json={"password": "test123"})
    assert response.status_code == 422
    
    # Test invalid email
    response = client.post("/api/v1/auth/register", json={
        "email": "invalid-email",
        "password": "test123"
    })
    assert response.status_code == 422
    
    # Test short password
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "123"
    })
    assert response.status_code == 422
