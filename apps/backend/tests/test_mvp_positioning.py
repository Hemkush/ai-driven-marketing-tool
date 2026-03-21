import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"positioning_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Positioning User"},
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _prepare_analysis(headers: dict) -> int:
    project = client.post(
        "/api/projects",
        json={"name": "Positioning Project", "description": "Positioning flow test"},
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
            "answer_text": "We create premium floral designs for weddings and private events.",
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
            "answer_text": "Engaged couples and event planners seeking high-end design.",
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
    return project_id


def test_mvp_positioning_generate_refine_and_latest():
    headers = _auth_headers()
    project_id = _prepare_analysis(headers)

    generated = client.post(
        "/api/mvp/positioning/generate",
        json={"project_id": project_id},
        headers=headers,
    )
    assert generated.status_code == 201
    first = generated.json()["positioning"]
    assert first["version"] == 1
    assert isinstance(first["positioning_statement"], str)
    assert len(first["positioning_statement"]) > 0

    refined = client.post(
        "/api/mvp/positioning/refine",
        json={
            "project_id": project_id,
            "owner_feedback": "Please emphasize premium service and reliability.",
        },
        headers=headers,
    )
    assert refined.status_code == 200
    second = refined.json()["positioning"]
    assert second["version"] == 2

    latest = client.get(f"/api/mvp/positioning/latest/{project_id}", headers=headers)
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert latest_payload["version"] == 2
    assert isinstance(latest_payload["positioning_statement"], str)
