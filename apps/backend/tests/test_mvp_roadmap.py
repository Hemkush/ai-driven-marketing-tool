import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"roadmap_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Roadmap User"},
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _prepare_strategy(headers: dict) -> int:
    project = client.post(
        "/api/projects",
        json={"name": "Roadmap Project", "description": "Roadmap generation test"},
        headers=headers,
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    session = client.post(
        "/api/mvp/questionnaire/sessions",
        json={"project_id": project_id},
        headers=headers,
    )
    assert session.status_code == 201
    session_id = session.json()["id"]

    r1 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your business",
            "answer_text": "We run a premium floral and event decor studio.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert r1.status_code == 201

    r2 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your customers",
            "answer_text": "Customers care about premium design, reliability, and fast response.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert r2.status_code == 201

    assert (
        client.post(
            "/api/mvp/analysis/run",
            json={"project_id": project_id},
            headers=headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/mvp/research/run",
            json={"project_id": project_id},
            headers=headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/mvp/personas/generate",
            json={"project_id": project_id},
            headers=headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/mvp/strategy/generate",
            json={"project_id": project_id},
            headers=headers,
        ).status_code
        == 201
    )
    return project_id


def test_mvp_roadmap_generation_and_latest():
    headers = _auth_headers()
    project_id = _prepare_strategy(headers)

    generated = client.post(
        "/api/mvp/roadmap/generate",
        json={"project_id": project_id},
        headers=headers,
    )
    assert generated.status_code == 201
    payload = generated.json()
    assert payload["status"] == "ready"
    assert payload["roadmap"]["duration_days"] == 90
    assert len(payload["roadmap"]["weekly_plan"]) == 12

    latest = client.get(f"/api/mvp/roadmap/latest/{project_id}", headers=headers)
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert latest_payload["roadmap"]["duration_days"] == 90
    assert len(latest_payload["roadmap"]["milestones"]) >= 3
