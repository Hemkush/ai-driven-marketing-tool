import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"analysis_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Analysis User"},
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_mvp_analysis_report_generation_and_latest_fetch():
    headers = _auth_headers()

    project = client.post(
        "/api/projects",
        json={"name": "Analysis Project", "description": "Segment analysis test"},
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
            "answer_text": "We are a local flower studio focused on wedding decor and subscriptions.",
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
            "answer_text": "Primary customers are engaged couples and office managers in nearby areas.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert q2.status_code == 201

    run = client.post(
        "/api/mvp/analysis/run",
        json={"project_id": project_id},
        headers=headers,
    )
    assert run.status_code == 201
    payload = run.json()
    assert payload["status"] == "ready"
    report = payload["report"]
    assert isinstance(report, dict)
    assert "analysis_source" in report
    # segment_attractiveness_analysis is only present when Google Places API
    # is configured; in CI (no key) the service returns a graceful fallback.
    if report.get("analysis_source") != "fallback":
        assert "segment_attractiveness_analysis" in report

    latest = client.get(f"/api/mvp/analysis/latest/{project_id}", headers=headers)
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert latest_payload["status"] == "ready"
    latest_report = latest_payload["report"]
    assert isinstance(latest_report, dict)
    assert "analysis_source" in latest_report
    if latest_report.get("analysis_source") != "fallback":
        assert "segment_attractiveness_analysis" in latest_report
