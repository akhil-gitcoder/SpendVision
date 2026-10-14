"""Pydantic schemas for transactions."""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_date: date
    description: str
    merchant: Optional[str] = None
    amount: float
    transaction_type: str
    category: Optional[CategoryOut] = None
    category_confidence: Optional[float] = None
    category_source: Optional[str] = None
    source: str
    created_at: datetime


class TransactionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TransactionOut]


class UploadRowError(BaseModel):
    row_number: int
    reason: str


class UploadResponse(BaseModel):
    filename: str
    total_rows: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    errors: list[UploadRowError] = Field(default_factory=list)
