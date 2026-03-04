from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_openapi():
    r = client.get("/openapi.json")
    assert r.status_code == 200

def test_metrics_exists():
    r = client.get("/metrics")
    assert r.status_code == 200
