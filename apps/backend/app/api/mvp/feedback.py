from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db import get_db
from app.models import OutputFeedback, User

from app.api.mvp.deps import FeedbackRequest

router = APIRouter(prefix="/api/mvp", tags=["feedback"])


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = OutputFeedback(
        project_id=payload.project_id,
        agent=payload.agent,
        quality_score=payload.quality_score,
        polarity=payload.polarity,
    )
    db.add(row)
    db.commit()
