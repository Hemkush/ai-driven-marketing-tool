from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.core.rate_limit import limiter
from app.core.security import require_internal_api_key
from app.db import get_db
from app.models import Generation, Project, User
from app.services.generator import generate_campaign_brief, generate_channel_assets
from app.services.storage import list_generations, save_generation

router = APIRouter(prefix="/api")


class CampaignRequest(BaseModel):
    product: str = Field(min_length=2, max_length=120)
    audience: str = Field(min_length=2, max_length=120)
    goal: str = Field(min_length=2, max_length=200)
    business_profile_id: int | None = None
    project_id: int | None = None


def _resolve_business_profile_id(
    business_profile_id: int | None,
    project_id: int | None,
) -> int | None:
    return business_profile_id or project_id


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    business_address: str | None = Field(default=None, max_length=500)

class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    business_address: str | None = Field(default=None, max_length=500)



@router.get("/ping")
def ping():
    return {"message": "pong"}


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    pending = db.query(PendingRegistration).filter(PendingRegistration.token == token).first()
    if not pending:
        # Maybe already verified
        raise HTTPException(status_code=400, detail="Invalid or expired verification link.")
    if datetime.now(timezone.utc) > pending.expires_at:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="Verification link has expired. Please register again.")

    # Create the real user now
    if not db.query(User).filter(User.email == pending.email).first():
        user = User(
            email=pending.email,
            password_hash=pending.password_hash,
            full_name=pending.full_name,
        )
        db.add(user)

    db.delete(pending)
    db.commit()
    return {"message": "Email verified successfully. You can now sign in."}


@router.post("/auth/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    pending = db.query(PendingRegistration).filter(PendingRegistration.email == email).first()
    # Always return 200 to avoid leaking whether email exists
    if not pending:
        return {"message": "If that email exists and is unverified, a new link has been sent."}

    token = secrets.token_urlsafe(48)
    pending.token = token
    pending.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()
    send_verification_email(email, token)
    return {"message": "If that email exists and is unverified, a new link has been sent."}


@router.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }


@router.post("/projects", status_code=status.HTTP_201_CREATED)
@router.post("/business-profiles", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        name=payload.name.strip(),
        description=payload.description,
        business_address=(payload.business_address or "").strip() or None,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "business_address": project.business_address,
        "owner_id": project.owner_id,
        "created_at": project.created_at.isoformat(),
    }


@router.get("/projects")
@router.get("/business-profiles")
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.id.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "business_address": p.business_address,
                "owner_id": p.owner_id,
                "created_at": p.created_at.isoformat(),
            }
            for p in projects
        ]
    }


@router.get("/projects/{project_id}")
@router.get("/business-profiles/{project_id}")
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Business profile not found")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "business_address": project.business_address,
        "owner_id": project.owner_id,
        "created_at": project.created_at.isoformat(),
    }


def _validate_project_access(
    db: Session,
    current_user: User,
    project_id: int | None,
) -> None:
    if project_id is None:
        return
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Business profile not found")


@router.post("/generate")
@limiter.limit("10/minute")
def generate_campaign(
    request: Request,
    payload: CampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        business_profile_id = _resolve_business_profile_id(
            payload.business_profile_id, payload.project_id
        )
        _validate_project_access(db, current_user, business_profile_id)
        result = generate_campaign_brief(
            product=payload.product,
            audience=payload.audience,
            goal=payload.goal,
        )
        save_generation(
            payload.model_dump(),
            result,
            project_id=business_profile_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/generate-assets")
@limiter.limit("10/minute")
def generate_assets(
    request: Request,
    payload: CampaignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        business_profile_id = _resolve_business_profile_id(
            payload.business_profile_id, payload.project_id
        )
        _validate_project_access(db, current_user, business_profile_id)
        result = generate_channel_assets(
            product=payload.product,
            audience=payload.audience,
            goal=payload.goal,
        )
        save_generation(
            payload.model_dump(),
            result,
            project_id=business_profile_id,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Asset generation failed: {str(e)}")


@router.get("/generations", dependencies=[Depends(require_internal_api_key)])
def get_generations(
    limit: int = Query(default=20, ge=1, le=100),
    project_id: int | None = Query(default=None, ge=1),
):
    return {"items": list_generations(limit=limit, project_id=project_id)}

@router.delete("/projects/{project_id}", status_code=204)
@router.delete("/business-profiles/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Business profile not found")

    (
        db.query(Generation)
        .filter(Generation.project_id == project.id)
        .update({Generation.project_id: None}, synchronize_session=False)
    )
    db.delete(project)
    db.commit()

@router.patch("/projects/{project_id}")
@router.patch("/business-profiles/{project_id}")
def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Business profile not found")

    if payload.name is not None:
        project.name = payload.name.strip()
    if payload.description is not None:
        project.description = payload.description
    if payload.business_address is not None:
        project.business_address = payload.business_address.strip() or None

    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "business_address": project.business_address,
        "owner_id": project.owner_id,
        "created_at": project.created_at.isoformat(),
    }
