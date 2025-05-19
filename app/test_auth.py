from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

@pytest.fixture
def test_register():
    response = client.post(
        "/register",
        json = {
                "name": "Иван Иванов",
                "email": "admin@admin.com",
                "password": "admin",
                "user_type": "ADMIN",
                "dancer_id": "None"
                }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "Иван Иванов"

@pytest.fixture
def test_login():
    response = client.post(
        "/login",
        json={"username": "admin@admin.com", "password": "admin"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
