import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"persona_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Persona User"},
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _prepare_research(headers: dict) -> int:
    project = client.post(
        "/api/projects",
        json={"name": "Persona Project", "description": "Persona generation test"},
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

    q1 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your business",
            "answer_text": "We run a creative flower brand focused on weddings and premium events.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert q1.status_code == 201

    q2 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your customers",
            "answer_text": "Customers care about design quality, trust, and smooth event execution.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert q2.status_code == 201

    analysis = client.post(
        "/api/mvp/analysis/run",
        json={"project_id": project_id},
        headers=headers,
    )
    assert analysis.status_code == 201

    research = client.post(
        "/api/mvp/research/run",
        json={"project_id": project_id},
        headers=headers,
    )
    assert research.status_code == 201
    return project_id


def test_mvp_persona_generation_and_listing():
    headers = _auth_headers()
    project_id = _prepare_research(headers)

    generated = client.post(
        "/api/mvp/personas/generate",
        json={"project_id": project_id},
        headers=headers,
    )
    assert generated.status_code == 201
    payload = generated.json()
    assert payload["status"] == "ready"
    assert payload["created_personas"] >= 2
    assert isinstance(payload["personas"], list)

    listed = client.get(f"/api/mvp/personas/{project_id}", headers=headers)
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) >= 2
    assert "basic_profile" in items[0]["profile"]
    assert "psychographic_profile" in items[0]["profile"]
    assert "behavioral_profile" in items[0]["profile"]
    assert "engagement_strategy" in items[0]["profile"]
