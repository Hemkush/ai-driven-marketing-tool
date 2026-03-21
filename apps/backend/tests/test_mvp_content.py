import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"content_user_{int(time.time() * 1000)}@example.com"


def _auth_headers() -> dict:
    email = _unique_email()
    password = "supersecure123"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Content User"},
    )
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _prepare_roadmap(headers: dict) -> int:
    project = client.post(
        "/api/projects",
        json={"name": "Content Project", "description": "Content generation test"},
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

    a1 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your business",
            "answer_text": "We are a boutique floral brand for premium events and weddings.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert a1.status_code == 201
    a2 = client.post(
        f"/api/mvp/questionnaire/sessions/{session_id}/responses",
        json={
            "question_text": "Tell me about your customers",
            "answer_text": "Customers expect premium quality, timely delivery, and creative execution.",
            "question_type": "open_ended",
            "source": "system",
        },
        headers=headers,
    )
    assert a2.status_code == 201

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
    assert (
        client.post(
            "/api/mvp/roadmap/generate",
            json={"project_id": project_id},
            headers=headers,
        ).status_code
        == 201
    )
    return project_id


def test_mvp_content_generation_and_asset_retrieval():
    headers = _auth_headers()
    project_id = _prepare_roadmap(headers)

    generated = client.post(
        "/api/mvp/content/generate",
        json={
            "project_id": project_id,
            "asset_type": "social_post",
            "prompt_text": "Create launch-week social content focused on premium trust.",
            "num_variants": 3,
        },
        headers=headers,
    )
    assert generated.status_code == 201
    payload = generated.json()
    assert payload["status"] == "ready"
    assert payload["generated_count"] >= 1
    first_asset_id = payload["assets"][0]["id"]

    listed = client.get(f"/api/mvp/content/assets/{project_id}", headers=headers)
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) >= 1

    fetched = client.get(f"/api/mvp/content/assets/item/{first_asset_id}", headers=headers)
    assert fetched.status_code == 200
    item_payload = fetched.json()
    assert item_payload["id"] == first_asset_id
    assert item_payload["project_id"] == project_id
