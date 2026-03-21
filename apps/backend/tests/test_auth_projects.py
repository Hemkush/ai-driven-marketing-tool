import time
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"user_{int(time.time() * 1000)}@example.com"


def test_register_login_and_projects_flow():
    email = _unique_email()

    register_resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "supersecure123",
            "full_name": "Test User",
        },
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["email"] == email

    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "supersecure123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_project_resp = client.post(
        "/api/projects",
        json={
            "name": "Launch Q2",
            "description": "Project for Q2 marketing",
            "business_address": "Seattle, WA",
        },
        headers=headers,
    )
    assert create_project_resp.status_code == 201
    project = create_project_resp.json()
    project_id = project["id"]
    assert project["business_address"] == "Seattle, WA"

    list_projects_resp = client.get("/api/projects", headers=headers)
    assert list_projects_resp.status_code == 200
    items = list_projects_resp.json()["items"]
    assert any(p["id"] == project_id for p in items)

    get_project_resp = client.get(f"/api/projects/{project_id}", headers=headers)
    assert get_project_resp.status_code == 200
    assert get_project_resp.json()["id"] == project_id
    assert get_project_resp.json()["business_address"] == "Seattle, WA"
