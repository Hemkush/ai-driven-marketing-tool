import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"mvp_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"

    register_resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "MVP User"},
    )
    assert register_resp.status_code == 201

    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_mvp_onboarding_next_questions():
    headers = _auth_headers()

    project_resp = client.post(
        "/api/projects",
        json={"name": "MVP Project", "description": "Onboarding flow test"},
        headers=headers,
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    session_resp = client.post(
        "/api/mvp/questionnaire/sessions",
        json={"project_id": project_id},
        headers=headers,
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    add_response = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your business",
            "answer_text": "We run a local flower shop focused on weddings and events.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert add_response.status_code == 201

    next_questions_resp = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/next-questions",
        headers=headers,
    )
    assert next_questions_resp.status_code == 200
    payload = next_questions_resp.json()
    assert payload["status"] == "ready"
    assert isinstance(payload["next_questions"], list)
    assert len(payload["next_questions"]) >= 1
    assert isinstance(payload["suggested_responses"], list)
    assert len(payload["suggested_responses"]) >= 1

    suggested_id = payload["suggested_responses"][0]["id"]

    accept_resp = client.post(
        f"/api/mvp/questionnaire/responses/{suggested_id}/accept",
        headers=headers,
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["source"] == "agent_accepted"

    reject_resp = client.post(
        f"/api/mvp/questionnaire/responses/{suggested_id}/reject",
        headers=headers,
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["source"] == "agent_rejected"


def test_chat_questions_do_not_repeat():
    headers = _auth_headers()

    project_resp = client.post(
        "/api/projects",
        json={"name": "Chat Repeat Guard", "description": "No-repeat question test"},
        headers=headers,
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    start_resp = client.post(
        "/api/mvp/questionnaire/chat/start",
        json={"project_id": project_id},
        headers=headers,
    )
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]
    first_q = start_resp.json()["messages"][0]["question_text"].strip()

    reply_1 = client.post(
        f"/api/mvp/questionnaire/chat/{session_id}/reply",
        json={
            "answer_text": (
                "We are BrightNest Home Organizing, helping busy families and professionals "
                "create functional, clutter-free spaces."
            )
        },
        headers=headers,
    )
    assert reply_1.status_code == 200
    second_q = reply_1.json()["next_question"]["question_text"].strip()
    assert second_q
    assert second_q.lower() != first_q.lower()

    reply_2 = client.post(
        f"/api/mvp/questionnaire/chat/{session_id}/reply",
        json={
            "answer_text": (
                "Our ideal customers are dual-income families and working professionals who "
                "need sustainable home organization systems."
            )
        },
        headers=headers,
    )
    assert reply_2.status_code == 200
    third_q = reply_2.json()["next_question"]["question_text"].strip()
    assert third_q
    assert third_q.lower() not in {first_q.lower(), second_q.lower()}


def test_analysis_important_points_are_concise_bullets():
    headers = _auth_headers()

    project_resp = client.post(
        "/api/projects",
        json={"name": "Chat Analysis Quality", "description": "Important points quality test"},
        headers=headers,
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    start_resp = client.post(
        "/api/mvp/questionnaire/chat/start",
        json={"project_id": project_id},
        headers=headers,
    )
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    long_customer_answer = (
        "1. A Clutter-Free, Functional Space\n"
        "They want rooms that are easy to use, easy to maintain, and visually calming.\n"
        "2. Time Savings & Convenience\n"
        "They do not have the time or energy to organize on their own.\n"
        "3. Long-Term Maintainability\n"
        "They want systems that help them stay organized over time."
    )
    reply_1 = client.post(
        f"/api/mvp/questionnaire/chat/{session_id}/reply",
        json={"answer_text": "We provide premium home organization services for busy families."},
        headers=headers,
    )
    assert reply_1.status_code == 200

    reply_2 = client.post(
        f"/api/mvp/questionnaire/chat/{session_id}/reply",
        json={"answer_text": long_customer_answer},
        headers=headers,
    )
    assert reply_2.status_code == 200
    analysis = reply_2.json()["analysis"]

    # In pytest, OPENAI path is disabled so this should be deterministic fallback.
    assert analysis["analysis_source"] == "fallback"
    points = analysis.get("important_points", [])
    assert isinstance(points, list)
    assert len(points) >= 1
    assert len(points) <= 5

    for p in points:
        assert isinstance(p, str)
        assert ":" in p
        assert "\n" not in p
        # Ensure concise bullet form, not full pasted paragraphs.
        assert len(p.split()) <= 15
