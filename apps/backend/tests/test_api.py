from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_ping():
    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.json()["message"] == "pong"

def test_generate_validation_error():
    payload = {"product": "A", "audience": "B", "goal": "C"}  # too short for your Field rules
    r = client.post("/api/generate", json=payload)
    assert r.status_code == 422
