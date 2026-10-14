"""Deterministic analytics endpoints - every number here is computed
directly from the database via pandas, with no AI involved."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.comparison import compute_month_comparison
from app.analytics.summary import compute_summary
from app.analytics.top_expenses import compute_top_expenses
from app.analytics.trends import compute_category_breakdown, compute_monthly_trend, VALID_GRANULARITIES
from app.database import get_db
from app.models import User
from app.schemas.analytics import (
    CategoryBreakdownResponse,
    MonthComparisonResponse,
    MonthlyTrendResponse,
    SummaryResponse,
    TopExpensesResponse,
)
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compute_summary(db, user.id, start_date, end_date)


@router.get("/monthly", response_model=MonthlyTrendResponse)
def get_monthly_trend(
    granularity: str = Query("monthly", description=f"One of {sorted(VALID_GRANULARITIES)}"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compute_monthly_trend(db, user.id, granularity)


@router.get("/categories", response_model=CategoryBreakdownResponse)
def get_category_breakdown(
    month: Optional[str] = Query(None, description="YYYY-MM, defaults to current month if omitted"),
    all_time: bool = Query(False, description="If true, ignore `month` and return all-time breakdown"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compute_category_breakdown(db, user.id, None if all_time else month)


@router.get("/comparison", response_model=MonthComparisonResponse)
def get_month_comparison(
    month: Optional[str] = Query(None, description="YYYY-MM, defaults to current month"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compute_month_comparison(db, user.id, month)


@router.get("/top-expenses", response_model=TopExpensesResponse)
def get_top_expenses(
    month: Optional[str] = Query(None, description="YYYY-MM, omit for all-time"),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return compute_top_expenses(db, user.id, month, limit)
