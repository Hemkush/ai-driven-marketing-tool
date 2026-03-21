import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"research_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Research User"},
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _prepare_analysis(headers: dict) -> int:
    project = client.post(
        "/api/projects",
        json={"name": "Research Project", "description": "Market research test"},
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
            "answer_text": "We provide premium floral services for weddings and corporate events.",
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
            "answer_text": "Our customers value design quality and on-time delivery.",
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


def test_mvp_research_run_and_latest():
    headers = _auth_headers()
    project_id = _prepare_analysis(headers)

    run = client.post(
        "/api/mvp/research/run",
        json={"project_id": project_id},
        headers=headers,
    )
    assert run.status_code == 201
    payload = run.json()
    assert payload["status"] == "ready"
    report = payload["report"]
    assert "target_customer_insights" in report
    assert "competitor_insights" in report
    assert "sources" in report
    assert len(report["sources"]) >= 1

    latest = client.get(f"/api/mvp/research/latest/{project_id}", headers=headers)
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert latest_payload["status"] == "ready"
    assert "sources" in latest_payload["report"]
