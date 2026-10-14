"""AI-powered endpoints: single-transaction categorization, spending
insights, and the natural-language finance assistant."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.insights import generate_insights
from app.ai.provider import LLMProvider
from app.database import get_db
from app.models import User
from app.schemas.ai import (
    CategorizeRequest,
    CategorizeResponse,
    ClearHistoryResponse,
    InsightsResponse,
    QueryHistoryResponse,
    QueryRequest,
    QueryResponse,
)
from app.services.categorization import categorize_transaction
from app.services.insights_data import build_insight_stats
from app.services.query_engine import clear_history, list_history, run_query
from app.utils.deps import get_current_user, get_provider

router = APIRouter()


@router.post("/categorize", response_model=CategorizeResponse)
def categorize(
    payload: CategorizeRequest,
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_provider),
):
    result = categorize_transaction(
        provider,
        payload.description,
        payload.merchant,
        payload.amount,
        payload.transaction_type,
    )
    return CategorizeResponse(**result)


@router.get("/insights", response_model=InsightsResponse)
def get_insights(
    month: Optional[str] = Query(None, description="YYYY-MM, defaults to current month"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_provider),
):
    stats = build_insight_stats(db, user.id, month)
    insights, ai_available = generate_insights(provider, stats)
    return InsightsResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        stats=stats,
        insights=insights,
        ai_available=ai_available,
    )


@router.post("/query", response_model=QueryResponse)
def ask_query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_provider),
):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = run_query(db, user.id, provider, question)
    return QueryResponse(**result)


@router.get("/query/history", response_model=QueryHistoryResponse)
def get_query_history(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Earlier Ask AI questions and answers for the current user, oldest first."""
    return QueryHistoryResponse(items=[QueryResponse(**m) for m in list_history(db, user.id, limit)])


@router.delete("/query/history", response_model=ClearHistoryResponse)
def delete_query_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ClearHistoryResponse(deleted=clear_history(db, user.id))
