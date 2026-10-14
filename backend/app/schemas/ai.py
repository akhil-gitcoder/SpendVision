"""Pydantic schemas for the AI layer (categorization, insights, NL query)."""
from typing import Optional

from pydantic import BaseModel, Field


class CategorizeRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    merchant: Optional[str] = None
    amount: Optional[float] = None
    transaction_type: str = Field(default="expense", pattern="^(income|expense)$")


class CategorizeResponse(BaseModel):
    category: str
    confidence: float
    source: str  # "rule" | "ai"


class InsightItem(BaseModel):
    title: str
    detail: str
    severity: str  # "info" | "positive" | "warning"


class InsightsResponse(BaseModel):
    generated_at: str
    stats: dict
    insights: list[InsightItem]
    ai_available: bool


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class QueryResponse(BaseModel):
    id: Optional[str] = None
    question: str
    intent: str
    data: dict
    answer: str
    ai_available: bool
    created_at: Optional[str] = None


class QueryHistoryResponse(BaseModel):
    items: list[QueryResponse]


class ClearHistoryResponse(BaseModel):
    deleted: int
