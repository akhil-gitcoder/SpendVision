"""Transaction upload, listing, and detail endpoints."""
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.database import get_db
from app.models import Category, Transaction, TransactionType, User
from app.schemas.transaction import TransactionListResponse, TransactionOut, UploadResponse, UploadRowError
from app.services.csv_import import CSVValidationError, import_transactions
from app.utils.deps import get_current_user, get_provider

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_provider),
):
    file_bytes = await file.read()
    try:
        result = import_transactions(db, user, file_bytes, file.filename or "upload.csv", provider)
    except CSVValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        # Never leak internals (e.g. DB connection strings) to the client.
        raise HTTPException(status_code=500, detail="Failed to process the uploaded file.") from exc

    return UploadResponse(
        filename=file.filename or "upload.csv",
        total_rows=result.total_rows,
        imported_count=result.imported_count,
        duplicate_count=result.duplicate_count,
        failed_count=result.failed_count,
        errors=[UploadRowError(row_number=e.row_number, reason=e.reason) for e in result.errors],
    )


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    search: Optional[str] = Query(None, max_length=255),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
):
    query = db.query(Transaction).filter(Transaction.user_id == user.id)

    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == TransactionType(transaction_type))
    if category:
        query = query.join(Category).filter(Category.name == category)
    if search:
        like = f"%{search}%"
        query = query.filter(Transaction.description.ilike(like))

    total = query.count()
    items = (
        query.order_by(desc(Transaction.transaction_date), desc(Transaction.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return TransactionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[TransactionOut.model_validate(t) for t in items],
    )


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    txn = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == user.id)
        .first()
    )
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return TransactionOut.model_validate(txn)
