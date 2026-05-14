"""
Tests for the Churn Prediction API.

Run with:
    pytest tests/ -v
    pytest tests/ -v --cov=app --cov=main --cov-report=term-missing
"""

import pytest
from litestar.testing import TestClient

from main import app
from app.model_utils import predict_churn


# ---------------------------------------------------------------------------
# Function Tests
# ---------------------------------------------------------------------------


def test_predict_churn_returns_binary():
    """Test that predict_churn returns 0 or 1"""
    sample_features = {
        "CreditScore": 600,
        "Geography": "Germany",
        "Gender": "Male",
        "Age": 35,
        "Tenure": 5,
        "Balance": 50000,
        "NumOfProducts": 2,
        "HasCrCard": 1,
        "IsActiveMember": 1,
        "EstimatedSalary": 60000
    }
    
    result = predict_churn(sample_features)
    assert result in [0, 1], f"Expected 0 or 1, got {result}"


# TODO 2 (bonus): Write another function test with edge-case inputs


# ---------------------------------------------------------------------------
# Endpoint Tests
# ---------------------------------------------------------------------------

def test_predict_endpoint():
    """Test POST /predict endpoint with valid input"""
    with TestClient(app=app) as client:
        payload = {
            "CreditScore": 600,
            "Geography": "Germany",
            "Gender": "Male",
            "Age": 35,
            "Tenure": 5,
            "Balance": 50000,
            "NumOfProducts": 2,
            "HasCrCard": 1,
            "IsActiveMember": 1,
            "EstimatedSalary": 60000
        }
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "prediction" in data
        assert data["prediction"] in [0, 1]


def test_health_endpoint():
    """Test GET /health endpoint"""
    with TestClient(app=app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


def test_home_endpoint():
    """Test GET / endpoint"""
    with TestClient(app=app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome" in data["message"]


# TODO 6 (bonus): Test that invalid input returns status 400
