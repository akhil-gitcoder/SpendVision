"""Unusual spending detection - a deterministic statistical check, not AI.
See app/analytics/anomalies.py for the algorithm."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.anomalies import detect_anomalies
from app.database import get_db
from app.models import User
from app.schemas.analytics import AnomalyResponse
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("", response_model=AnomalyResponse)
def get_anomalies(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    anomalies = detect_anomalies(db, user.id)
    return AnomalyResponse(anomalies=anomalies)
