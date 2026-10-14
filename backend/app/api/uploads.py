import hashlib
import io
import uuid
from datetime import datetime
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.database import get_db
from app.models import Transaction, UploadDocument, UploadImport, User
from app.schemas.upload_document import SavedUpload, UploadDocumentOut, UploadPreview
from app.services.csv_import import (
    CSVValidationError, MAX_FILE_SIZE_BYTES, _validate_and_read, import_transactions,
)
from app.utils.deps import get_current_user, get_provider

router = APIRouter()


@router.get("", response_model=list[UploadDocumentOut])
def list_uploads(
    year: int = Query(..., ge=1900, le=2100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(UploadDocument).filter(
        UploadDocument.user_id == user.id,
        UploadDocument.month.startswith(f"{year}-"),
    ).order_by(UploadDocument.uploaded_at.desc()).all()


@router.post("", response_model=SavedUpload, status_code=201)
def save_upload(
    month: str = Form(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_provider),
):
    if not 1900 <= int(month[:4]) <= 2100:
        raise HTTPException(400, "Select a year between 1900 and 2100.")
    filename = (file.filename or "transactions.csv").replace("\\", "/").split("/")[-1]
    if not filename or len(filename) > 255 or any(ord(c) < 32 for c in filename):
        raise HTTPException(400, "Use a filename of 1–255 characters without control characters.")
    content = file.file.read(MAX_FILE_SIZE_BYTES + 1)
    try:
        dataframe = _validate_and_read(content, filename)
    except CSVValidationError as exc:
        raise HTTPException(400, str(exc)) from exc

    # Never rewrite dates to force transactions into the selected month.
    for value in dataframe["date"]:
        parsed = pd.to_datetime(value, errors="coerce")
        if not pd.isna(parsed) and parsed.strftime("%Y-%m") != month:
            label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
            raise HTTPException(400, f"This file contains dates outside {label}. Choose the matching month or split the CSV by month.")

    checksum = hashlib.sha256(content).hexdigest()
    # PostgreSQL serializes uploads for this account to protect duplicate checks.
    db.query(User).filter(User.id == user.id).with_for_update().one()
    existing = db.query(UploadDocument).filter_by(
        user_id=user.id, month=month, checksum=checksum,
    ).first()
    if existing:
        raise HTTPException(409, "This exact file is already saved. Use View CSV to open it, or select another file.")
    try:
        result = import_transactions(db, user, content, filename, provider, commit=False)
        document = UploadDocument(
            user_id=user.id, month=month, filename=filename,
            checksum=checksum, size_bytes=len(content), content=content,
            total_rows=result.total_rows, imported_count=result.imported_count,
            duplicate_count=result.duplicate_count, failed_count=result.failed_count,
            errors=[{"row_number": e.row_number, "reason": e.reason} for e in result.errors],
        )
        db.add(document)
        # Original document and its transactions succeed or roll back together.
        db.flush()

        db.add(
            UploadImport(
                document_id=document.id,
                transaction_ids=result.transaction_ids,
            )
        )
        db.commit()
        db.refresh(document)
        return document
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Upload conflicted with another request. Refresh the file list and try again.") from exc
    except Exception:
        db.rollback()
        raise


def owned_document(db: Session, user: User, document_id: uuid.UUID) -> UploadDocument:
    document = db.query(UploadDocument).filter_by(id=document_id, user_id=user.id).first()
    if document is None:
        raise HTTPException(404, "Uploaded file not found.")
    return document


@router.get("/{document_id}/preview", response_model=UploadPreview)
def preview_upload(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    document = owned_document(db, user, document_id)
    frame = pd.read_csv(io.BytesIO(document.content), dtype=str, keep_default_na=False, nrows=101)
    return UploadPreview(
        document=SavedUpload.model_validate(document),
        columns=[str(c)[:500] for c in frame.columns[:20]],
        rows=[[str(v)[:500] for v in row] for row in frame.iloc[:100, :20].itertuples(index=False, name=None)],
        has_more=len(frame) > 100 or len(frame.columns) > 20,
    )


@router.get("/{document_id}/download")
def download_upload(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    document = owned_document(db, user, document_id)
    return Response(
        content=document.content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(document.filename, safe='')}",
            "Cache-Control": "no-store",
        },
    )

@router.delete("/{document_id}")
def delete_upload(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Serialize uploads and deletions for this account.
    db.query(User).filter(
        User.id == user.id
    ).with_for_update().one()

    # Returns 404 if this file belongs to another account.
    document = owned_document(db, user, document_id)
    tracked = db.get(UploadImport, document.id)

    if tracked is None and document.imported_count > 0:
        raise HTTPException(
            409,
            "This older upload has no transaction links. "
            "Its file and transactions were left unchanged "
            "because automatic deletion would be unsafe.",
        )

    try:
        transaction_ids = (
            [uuid.UUID(value) for value in tracked.transaction_ids]
            if tracked
            else []
        )

        deleted = 0

        # Small batches avoid database query parameter limits.
        for start in range(0, len(transaction_ids), 500):
            deleted += db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.id.in_(
                    transaction_ids[start:start + 500]
                ),
            ).delete(synchronize_session=False)

        if tracked is not None:
            db.delete(tracked)
            db.flush()

        db.delete(document)

        # File and transactions are deleted together.
        db.commit()

        return {
            "deleted_document_id": str(document_id),
            "deleted_transactions": deleted,
        }

    except Exception:
        db.rollback()
        raise