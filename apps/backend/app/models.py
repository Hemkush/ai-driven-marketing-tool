from __future__ import annotations

from sqlalchemy import String, Text, DateTime, func, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - safety fallback when dependency is absent
    def Vector(_dim: int):  # type: ignore
        return Text()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    projects: Mapped[list[Project]] = relationship(back_populates="owner")


class PipelineRun(Base):
    """Traces every agent invocation — start time, end time, status, tokens used.

    Lets you answer: which step do users drop off at? Which agent is slowest?
    What's the end-to-end time for a full pipeline run?
    """
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    step: Mapped[str] = mapped_column(String(100), nullable=False)      # e.g. "competitive_benchmarker"
    status: Mapped[str] = mapped_column(String(20), nullable=False)     # success | error | cached
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # tokens, cache_key, etc.


class LLMCache(Base):
    """DB-backed response cache for expensive LLM + API calls.

    cache_key  = SHA256(agent + sorted canonical input)
    payload    = JSON-serialised LLM output
    TTL is enforced in application code (not a DB constraint) so old rows
    can be queried for analytics / audit before being pruned.
    """
    __tablename__ = "llm_cache"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    agent: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PendingRegistration(Base):
    """Holds signups until email is verified. Deleted on verify or expiry."""
    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="projects")
    generations: Mapped[list[Generation]] = relationship(back_populates="project")
    questionnaire_sessions: Mapped[list[QuestionnaireSession]] = relationship(
        back_populates="project"
    )
    analysis_reports: Mapped[list[AnalysisReport]] = relationship(back_populates="project")
    positioning_statements: Mapped[list[PositioningStatement]] = relationship(
        back_populates="project"
    )
    research_reports: Mapped[list[ResearchReport]] = relationship(back_populates="project")
    personas: Mapped[list[PersonaProfile]] = relationship(back_populates="project")
    channel_strategies: Mapped[list[ChannelStrategy]] = relationship(
        back_populates="project"
    )
    roadmap_plans: Mapped[list[RoadmapPlan]] = relationship(back_populates="project")
    media_assets: Mapped[list[MediaAsset]] = relationship(back_populates="project")


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"), nullable=True, index=True
    )
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[Project | None] = relationship(back_populates="generations")


class QuestionnaireSession(Base):
    __tablename__ = "questionnaire_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="in_progress", nullable=False)
    conversation_analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="questionnaire_sessions")
    responses: Mapped[list[QuestionnaireResponse]] = relationship(back_populates="session")


class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=False, index=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(40), default="open_ended", nullable=False)
    question_options_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="system", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    session: Mapped[QuestionnaireSession] = relationship(back_populates="responses")


class MemoryChunk(Base):
    __tablename__ = "memory_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    response_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_responses.id"), nullable=True, index=True
    )
    source_type: Mapped[str] = mapped_column(String(40), default="questionnaire_response", nullable=False)
    topic_tag: Mapped[str | None] = mapped_column(String(80), nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="analysis_reports")


class PositioningStatement(Base):
    __tablename__ = "positioning_statements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    statement_text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="positioning_statements")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="research_reports")


class PersonaProfile(Base):
    __tablename__ = "persona_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    persona_name: Mapped[str] = mapped_column(String(160), nullable=False)
    persona_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="personas")


class ChannelStrategy(Base):
    __tablename__ = "channel_strategies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    strategy_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="channel_strategies")


class RoadmapPlan(Base):
    __tablename__ = "roadmap_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="roadmap_plans")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    source_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("questionnaire_sessions.id"), nullable=True, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(80), nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="created", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="media_assets")
