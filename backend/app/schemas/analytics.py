"""Pydantic schemas for analytics endpoints. These represent deterministic,
backend-calculated figures (as opposed to AI-generated text)."""
from typing import Optional

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    total_savings: float
    savings_rate: float
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    transaction_count: int


class MonthlyPoint(BaseModel):
    period: str  # e.g. "2026-08" or "2026-08-01" depending on granularity
    income: float
    expenses: float


class MonthlyTrendResponse(BaseModel):
    granularity: str
    points: list[MonthlyPoint]


class CategoryBreakdownItem(BaseModel):
    category: str
    amount: float
    percent: float


class CategoryBreakdownResponse(BaseModel):
    total_expenses: float
    items: list[CategoryBreakdownItem]


class CategoryChangeItem(BaseModel):
    category: str
    current_amount: float
    previous_amount: float
    change_percent: Optional[float]  # None when previous was 0


class MonthComparisonResponse(BaseModel):
    current_month: str
    previous_month: str
    current_total: float
    previous_total: float
    change_percent: Optional[float]
    category_changes: list[CategoryChangeItem]


class TopExpenseItem(BaseModel):
    id: str
    transaction_date: str
    description: str
    merchant: Optional[str]
    category: Optional[str]
    amount: float


class TopExpensesResponse(BaseModel):
    items: list[TopExpenseItem]


class AnomalyItem(BaseModel):
    transaction_id: str
    transaction_date: str
    description: str
    merchant: Optional[str]
    category: Optional[str]
    amount: float
    typical_range_low: float
    typical_range_high: float
    reason: str


class AnomalyResponse(BaseModel):
    anomalies: list[AnomalyItem]
