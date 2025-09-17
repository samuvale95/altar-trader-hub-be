"""
Tests for portfolio API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_get_portfolio_overview(client: TestClient, auth_headers):
    """Test getting portfolio overview."""
    response = client.get("/api/v1/portfolio/overview", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "total_value" in data
    assert "total_pnl" in data
    assert "total_pnl_percentage" in data
    assert "active_positions" in data
    assert "total_positions" in data


def test_create_portfolio(client: TestClient, auth_headers, test_portfolio_data):
    """Test creating a portfolio."""
    response = client.post("/api/v1/portfolio/portfolios", 
                          json=test_portfolio_data, 
                          headers=auth_headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == test_portfolio_data["name"]
    assert data["description"] == test_portfolio_data["description"]
    assert "id" in data
    assert "user_id" in data


def test_get_portfolios(client: TestClient, auth_headers):
    """Test getting user portfolios."""
    response = client.get("/api/v1/portfolio/portfolios", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_get_portfolio(client: TestClient, auth_headers, test_portfolio_data):
    """Test getting a specific portfolio."""
    # Create portfolio first
    create_response = client.post("/api/v1/portfolio/portfolios", 
                                json=test_portfolio_data, 
                                headers=auth_headers)
    assert create_response.status_code == 201
    
    portfolio_id = create_response.json()["id"]
    
    # Get portfolio
    response = client.get(f"/api/v1/portfolio/portfolios/{portfolio_id}", 
                         headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == portfolio_id
    assert data["name"] == test_portfolio_data["name"]


def test_get_portfolio_not_found(client: TestClient, auth_headers):
    """Test getting non-existent portfolio."""
    response = client.get("/api/v1/portfolio/portfolios/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "Portfolio not found" in response.json()["detail"]


def test_update_portfolio(client: TestClient, auth_headers, test_portfolio_data):
    """Test updating a portfolio."""
    # Create portfolio first
    create_response = client.post("/api/v1/portfolio/portfolios", 
                                json=test_portfolio_data, 
                                headers=auth_headers)
    assert create_response.status_code == 201
    
    portfolio_id = create_response.json()["id"]
    
    # Update portfolio
    update_data = {"name": "Updated Portfolio", "description": "Updated description"}
    response = client.put(f"/api/v1/portfolio/portfolios/{portfolio_id}", 
                         json=update_data, 
                         headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


def test_delete_portfolio(client: TestClient, auth_headers, test_portfolio_data):
    """Test deleting a portfolio."""
    # Create portfolio first
    create_response = client.post("/api/v1/portfolio/portfolios", 
                                json=test_portfolio_data, 
                                headers=auth_headers)
    assert create_response.status_code == 201
    
    portfolio_id = create_response.json()["id"]
    
    # Delete portfolio
    response = client.delete(f"/api/v1/portfolio/portfolios/{portfolio_id}", 
                           headers=auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_get_positions(client: TestClient, auth_headers):
    """Test getting positions."""
    response = client.get("/api/v1/portfolio/positions", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_get_balances(client: TestClient, auth_headers):
    """Test getting balances."""
    response = client.get("/api/v1/portfolio/balances", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_create_duplicate_portfolio(client: TestClient, auth_headers, test_portfolio_data):
    """Test creating duplicate portfolio name."""
    # Create first portfolio
    response = client.post("/api/v1/portfolio/portfolios", 
                          json=test_portfolio_data, 
                          headers=auth_headers)
    assert response.status_code == 201
    
    # Try to create portfolio with same name
    response = client.post("/api/v1/portfolio/portfolios", 
                          json=test_portfolio_data, 
                          headers=auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_portfolio_unauthorized(client: TestClient):
    """Test portfolio endpoints without authentication."""
    response = client.get("/api/v1/portfolio/overview")
    assert response.status_code == 401
    
    response = client.get("/api/v1/portfolio/portfolios")
    assert response.status_code == 401
    
    response = client.post("/api/v1/portfolio/portfolios", json={})
    assert response.status_code == 401
