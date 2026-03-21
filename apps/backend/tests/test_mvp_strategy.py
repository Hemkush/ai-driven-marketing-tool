import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"strategy_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Strategy User"},
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _prepare_personas(headers: dict) -> int:
    project = client.post(
        "/api/projects",
        json={"name": "Strategy Project", "description": "Channel strategy test"},
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

    resp1 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your business",
            "answer_text": "We deliver premium floral experiences for weddings and events.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your customers",
            "answer_text": "Customers expect reliable execution, style, and easy communication.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert resp2.status_code == 201

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

    personas = client.post(
        "/api/mvp/personas/generate",
        json={"project_id": project_id},
        headers=headers,
    )
    assert personas.status_code == 201
    return project_id


def test_mvp_strategy_generation_and_latest():
    headers = _auth_headers()
    project_id = _prepare_personas(headers)

    generated = client.post(
        "/api/mvp/strategy/generate",
        json={"project_id": project_id},
        headers=headers,
    )
    assert generated.status_code == 201
    payload = generated.json()
    assert payload["status"] == "ready"
    assert "prioritized_channels" in payload["strategy"]
    assert len(payload["strategy"]["prioritized_channels"]) >= 1

    latest = client.get(f"/api/mvp/strategy/latest/{project_id}", headers=headers)
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert "strategy" in latest_payload
    assert "prioritized_channels" in latest_payload["strategy"]
