"""
Questionnaire / Marketing Discovery routes.
Covers session management, chat flow, response CRUD, and workflow summary.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db import get_db
from app.models import QuestionnaireResponse, QuestionnaireSession, User
from app.services.onboarding_interviewer import (
    analyze_chat_response,
    generate_next_chat_question,
    generate_next_questions_structured,
)
from app.services.memory_store import store_response_memory

from .deps import (
    QuestionnaireChatFinishRequest,
    QuestionnaireChatReplyRequest,
    QuestionnaireChatStartRequest,
    QuestionnaireResponseCreateRequest,
    QuestionnaireResponseUpdateRequest,
    QuestionnaireSessionCreateRequest,
    _build_session_workflow_snapshot,
    _chat_topic_coverage,
    _create_chat_question,
    _is_duplicate_question,
    _load_question_options,
    _owned_project_or_404,
    _pick_non_duplicate_question,
    _resolve_business_profile_id,
    _seed_default_business_questions,
    _serialize_response,
    _serialize_session_summary,
)

router = APIRouter(prefix="/api/mvp", tags=["questionnaire"])

DEFAULT_BUSINESS_PROFILE_QUESTIONS = [
    {"question_text": "Tell me about your business.", "question_type": "open_ended", "question_options": []},
    {"question_text": "Tell me about your customer.", "question_type": "open_ended", "question_options": []},
    {"question_text": "Where is your business located or primarily operating?", "question_type": "mcq", "question_options": ["Local", "Regional", "Online"]},
    {"question_text": "What is your primary product or service?", "question_type": "open_ended", "question_options": []},
    {"question_text": "What specific customer problem does your product or service solve?", "question_type": "open_ended", "question_options": []},
    {"question_text": "What makes your business different from competitors?", "question_type": "open_ended", "question_options": []},
    {"question_text": "Who are your top 3 competitors?", "question_type": "open_ended", "question_options": []},
    {"question_text": "How do customers currently find you?", "question_type": "mcq", "question_options": ["Social media", "Word of mouth", "Paid ads", "Search/SEO", "Partnerships or referrals", "Other"]},
    {"question_text": "Why do customers choose you over alternatives?", "question_type": "mcq", "question_options": ["Price", "Quality", "Convenience", "Expertise", "Customization"]},
    {"question_text": "How would you estimate your current monthly marketing budget?", "question_type": "mcq", "question_options": ["No dedicated budget yet", "Under $1,000", "$1,000-$5,000", "$5,000-$15,000", "$15,000+"]},
    {"question_text": "What is your top business goal for the next 12 months?", "question_type": "open_ended", "question_options": []},
]


@router.get("/questionnaire/templates/business-profile")
def get_business_profile_template():
    return {"items": DEFAULT_BUSINESS_PROFILE_QUESTIONS}


@router.post("/questionnaire/sessions", status_code=status.HTTP_201_CREATED)
def create_questionnaire_session(
    payload: QuestionnaireSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(payload.business_profile_id, payload.project_id)
    _owned_project_or_404(db, current_user, business_profile_id)
    session = QuestionnaireSession(project_id=business_profile_id, status="in_progress")
    db.add(session)
    db.flush()
    _seed_default_business_questions(db, session)
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
    }


@router.post("/questionnaire/chat/start", status_code=status.HTTP_201_CREATED)
def start_questionnaire_chat(
    payload: QuestionnaireChatStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business_profile_id = _resolve_business_profile_id(payload.business_profile_id, payload.project_id)
    _owned_project_or_404(db, current_user, business_profile_id)

    session = QuestionnaireSession(project_id=business_profile_id, status="in_progress")
    db.add(session)
    db.flush()

    first = _create_chat_question(
        db=db,
        session_id=session.id,
        sequence_no=1,
        question_text="Tell me about your business.",
        source="chatbot_seeded",
    )
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "current_question": _serialize_response(first),
        "messages": [
            {
                "role": "assistant",
                "response_id": first.id,
                "sequence_no": first.sequence_no,
                "question_text": first.question_text,
                "question_type": first.question_type,
                "question_options": [],
                "source": first.source,
            }
        ],
    }


@router.get("/questionnaire/sessions/{session_id}")
def get_questionnaire_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    return {
        "id": session.id,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "responses": [_serialize_response(r) for r in responses],
    }


@router.get("/questionnaire/sessions/by-business-profile/{project_id}")
def list_questionnaire_sessions_for_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_project_or_404(db, current_user, project_id)
    sessions = (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.project_id == project_id)
        .order_by(QuestionnaireSession.updated_at.desc(), QuestionnaireSession.id.desc())
        .all()
    )

    items = []
    for session in sessions:
        responses = (
            db.query(QuestionnaireResponse)
            .filter(QuestionnaireResponse.session_id == session.id)
            .order_by(QuestionnaireResponse.sequence_no.asc())
            .all()
        )
        items.append(_serialize_session_summary(session, responses))

    latest = items[0] if items else None
    return {"items": items, "latest_session_id": latest["id"] if latest else None}


@router.get("/workflow/session-summary/{session_id}")
def get_session_workflow_summary(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    project = _owned_project_or_404(db, current_user, session.project_id)
    payload = _build_session_workflow_snapshot(db, project, session)
    return {
        "business_profile_id": project.id,
        "project_id": project.id,
        "business_profile_name": project.name,
        "business_location": project.business_address,
        **payload,
    }


@router.get("/questionnaire/chat/{session_id}")
def get_questionnaire_chat(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    project = _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    if not responses:
        raise HTTPException(status_code=404, detail="No chat messages found for this session")

    messages = []
    for r in responses:
        messages.append({
            "role": "assistant",
            "response_id": r.id,
            "sequence_no": r.sequence_no,
            "question_text": r.question_text,
            "question_type": r.question_type,
            "question_options": _load_question_options(r.question_options_json),
            "source": r.source,
        })
        if (r.answer_text or "").strip():
            messages.append({
                "role": "user",
                "response_id": r.id,
                "sequence_no": r.sequence_no,
                "answer_text": r.answer_text,
            })

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "messages": messages,
        "current_question": _serialize_response(responses[-1]),
        "coverage": _chat_topic_coverage(responses),
        "analysis": analyze_chat_response(
            [
                {"question_text": r.question_text, "answer_text": r.answer_text,
                 "question_type": r.question_type, "source": r.source}
                for r in responses if (r.answer_text or "").strip()
            ],
            business_context={"business_location": project.business_address},
        ),
    }


@router.post("/questionnaire/chat/{session_id}/reply")
def reply_questionnaire_chat(
    session_id: int,
    payload: QuestionnaireChatReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    project = _owned_project_or_404(db, current_user, session.project_id)
    if session.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Interview is already completed. Start a new chat session to continue.",
        )

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    if not responses:
        raise HTTPException(status_code=400, detail="Chat session is not initialized")

    current = responses[-1]
    answer_text = payload.answer_text.strip()
    if not answer_text:
        raise HTTPException(status_code=400, detail="answer_text is required")

    current.answer_text = answer_text
    store_response_memory(
        db,
        project_id=session.project_id,
        session_id=session.id,
        response_id=current.id,
        question_text=current.question_text,
        answer_text=current.answer_text,
    )

    answered_payload = [
        {"id": r.id, "sequence_no": r.sequence_no, "question_text": r.question_text,
         "answer_text": r.answer_text, "question_type": r.question_type, "source": r.source}
        for r in responses if (r.answer_text or "").strip()
    ]
    analysis_payload = analyze_chat_response(
        answered_payload,
        business_context={"business_location": project.business_address},
    )
    session.conversation_analysis_json = json.dumps(analysis_payload)

    # Persist geographical_range to project so downstream agents can use it
    extracted_range = analysis_payload.get("geographical_range", "")
    if extracted_range and extracted_range not in ("Not provided", ""):
        project.geographical_range = extracted_range[:500]

    existing_questions = [r.question_text for r in responses]
    next_question = generate_next_chat_question(answered_payload)
    next_question_text = str(next_question.get("question_text", "")).strip()
    if not next_question_text:
        next_question_text = "What is your biggest growth bottleneck right now?"

    if _is_duplicate_question(next_question_text, existing_questions):
        fallback_attempts = [
            "Who is your ideal customer, and what are they trying to achieve?",
            "Who are your top competitors, and where are they stronger than you?",
            "What monthly budget can you dedicate to marketing and growth?",
            "What is your current average customer acquisition cost, if known?",
            "What is your most important business plan or goal in the next 12 months?",
            "What is your biggest growth bottleneck right now?",
            "Which channel has brought your best-quality leads in the last 90 days?",
            "What proof points or testimonials do customers mention before purchasing?",
            "Which customer segment is most profitable for your business today?",
        ]
        next_question_text = _pick_non_duplicate_question(existing_questions, fallback_attempts)

    next_row = _create_chat_question(
        db=db,
        session_id=session.id,
        sequence_no=current.sequence_no + 1,
        question_text=next_question_text,
        source="chatbot_generated",
    )
    db.commit()
    db.refresh(current)
    db.refresh(next_row)

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "saved_response": {
            "id": current.id,
            "sequence_no": current.sequence_no,
            "question_text": current.question_text,
            "answer_text": current.answer_text,
            "question_type": current.question_type,
            "source": current.source,
            "updated_at": current.updated_at.isoformat(),
        },
        "next_question": _serialize_response(next_row),
        "coverage": _chat_topic_coverage(responses),
        "analysis": analysis_payload,
    }


@router.post("/questionnaire/chat/{session_id}/finish")
def finish_questionnaire_chat(
    session_id: int,
    payload: QuestionnaireChatFinishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    answered_count = len([r for r in responses if (r.answer_text or "").strip()])
    if answered_count < 3 and not payload.force:
        raise HTTPException(
            status_code=400,
            detail="Please answer at least 3 questions before finishing the interview.",
        )

    coverage = _chat_topic_coverage(responses)
    session.status = "completed"
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "business_profile_id": session.project_id,
        "project_id": session.project_id,
        "answered_count": answered_count,
        "coverage": coverage,
        "missing_topics": [k for k, v in coverage.items() if not v],
    }


@router.post("/questionnaire/sessions/{session_id}/responses", status_code=status.HTTP_201_CREATED)
def add_questionnaire_response(
    session_id: int,
    payload: QuestionnaireResponseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    last = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.desc())
        .first()
    )
    next_sequence = (last.sequence_no + 1) if last else 1

    question_type = payload.question_type.strip().lower()
    if question_type not in {"open_ended", "mcq"}:
        raise HTTPException(status_code=400, detail="question_type must be open_ended or mcq")

    options = [x.strip() for x in payload.question_options if x.strip()]
    if question_type == "mcq" and len(options) < 2:
        raise HTTPException(status_code=400, detail="MCQ requires at least 2 options")
    if question_type == "mcq" and payload.answer_text and payload.answer_text not in options:
        raise HTTPException(status_code=400, detail="MCQ answer must match one option")

    response = QuestionnaireResponse(
        session_id=session.id,
        sequence_no=next_sequence,
        question_text=payload.question_text.strip(),
        answer_text=payload.answer_text,
        question_type=question_type,
        question_options_json=json.dumps(options if question_type == "mcq" else []),
        source=payload.source,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    result = _serialize_response(response)
    result["session_id"] = response.session_id
    return result


@router.patch("/questionnaire/responses/{response_id}")
def update_questionnaire_response(
    response_id: int,
    payload: QuestionnaireResponseUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = db.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    session = db.get(QuestionnaireSession, response.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    answer_text = payload.answer_text.strip()
    if response.question_type == "mcq":
        options = _load_question_options(response.question_options_json)
        if options and answer_text not in options:
            raise HTTPException(status_code=400, detail="MCQ answer must match one option")

    response.answer_text = answer_text
    db.commit()
    db.refresh(response)
    return {
        "id": response.id,
        "session_id": response.session_id,
        "answer_text": response.answer_text,
        "updated_at": response.updated_at.isoformat(),
    }


@router.post("/questionnaire/sessions/{session_id}/next-questions")
def generate_next_questions_contract(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import json as _json
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)

    responses = (
        db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.session_id == session.id)
        .order_by(QuestionnaireResponse.sequence_no.asc())
        .all()
    )
    response_payload = [
        {"id": r.id, "question_text": r.question_text, "answer_text": r.answer_text,
         "question_type": r.question_type, "source": r.source}
        for r in responses if (r.answer_text or "").strip()
    ]
    questions = generate_next_questions_structured(response_payload, max_questions=3)

    existing_questions = [r.question_text for r in responses]
    last = responses[-1] if responses else None
    next_sequence = (last.sequence_no + 1) if last else 1
    created_suggestions = []

    for question in questions:
        question_text = str(question.get("question_text", "")).strip()
        question_type = str(question.get("question_type", "open_ended")).strip().lower()
        if question_type not in {"open_ended", "mcq"}:
            question_type = "open_ended"
        options = [x.strip() for x in question.get("question_options", []) if x.strip()]
        if question_type == "mcq" and len(options) < 2:
            question_type = "open_ended"
            options = []
        if _is_duplicate_question(question_text, existing_questions):
            continue
        row = QuestionnaireResponse(
            session_id=session.id,
            sequence_no=next_sequence,
            question_text=question_text,
            answer_text="",
            question_type=question_type,
            question_options_json=_json.dumps(options if question_type == "mcq" else []),
            source="agent_suggested",
        )
        db.add(row)
        db.flush()
        created = _serialize_response(row)
        created_suggestions.append({
            "id": created["id"],
            "sequence_no": created["sequence_no"],
            "question_text": created["question_text"],
            "question_type": created["question_type"],
            "question_options": created["question_options"],
            "source": created["source"],
        })
        existing_questions.append(question_text)
        next_sequence += 1
    db.commit()

    return {
        "session_id": session.id,
        "agent_id": "onboarding_interviewer",
        "status": "ready",
        "next_questions": [r["question_text"] for r in created_suggestions],
        "suggested_responses": created_suggestions,
    }


@router.post("/questionnaire/responses/{response_id}/accept")
def accept_suggested_question(
    response_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = db.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    session = db.get(QuestionnaireSession, response.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)
    if not response.source.startswith("agent_"):
        raise HTTPException(status_code=400, detail="Only agent suggestions can be accepted")

    response.source = "agent_accepted"
    db.commit()
    db.refresh(response)
    return {"id": response.id, "session_id": response.session_id,
            "question_text": response.question_text, "source": response.source}


@router.post("/questionnaire/responses/{response_id}/reject")
def reject_suggested_question(
    response_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = db.get(QuestionnaireResponse, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    session = db.get(QuestionnaireSession, response.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _owned_project_or_404(db, current_user, session.project_id)
    if not response.source.startswith("agent_"):
        raise HTTPException(status_code=400, detail="Only agent suggestions can be rejected")

    response.source = "agent_rejected"
    db.commit()
    db.refresh(response)
    return {"id": response.id, "session_id": response.session_id,
            "question_text": response.question_text, "source": response.source}
