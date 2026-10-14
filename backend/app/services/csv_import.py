"""
CSV transaction import.

Expected columns (case-insensitive, order doesn't matter): date, description, amount, type
(type is "income" or "expense"). See sample-data/sample_transactions.csv for a full example.

The importer is deliberately defensive: a single malformed row never aborts
the whole upload. Each row is validated independently and bad rows are
collected as errors rather than raised as exceptions.
"""
import io
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.models import Category, Transaction, TransactionSource, TransactionType, User
from app.services.categorization import categorize_transaction

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"date", "description", "amount", "type"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB is plenty for a personal-finance CSV
MAX_ERRORS_RETURNED = 100


class CSVValidationError(Exception):
    """Raised for whole-file problems (bad format, missing columns, empty file)."""


@dataclass
class RowError:
    row_number: int
    reason: str


@dataclass
class ImportResult:
    total_rows: int = 0
    imported_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    errors: list[RowError] = field(default_factory=list)
    transaction_ids: list[str] = field(default_factory=list)


def _validate_and_read(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if not filename.lower().endswith(".csv"):
        raise CSVValidationError("Only .csv files are supported.")

    if len(file_bytes) == 0:
        raise CSVValidationError("The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise CSVValidationError("File is too large (max 5 MB).")

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:  # noqa: BLE001
        raise CSVValidationError(f"Could not parse file as CSV: {exc}") from exc

    if df.empty:
        raise CSVValidationError("The CSV file contains no data rows.")

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise CSVValidationError(
            f"Missing required column(s): {', '.join(sorted(missing))}. "
            f"Expected columns: {', '.join(sorted(REQUIRED_COLUMNS))}."
        )

    return df


def _parse_row(row: pd.Series) -> dict:
    """Returns a clean dict, or raises ValueError with a human-readable reason."""
    description = str(row.get("description", "")).strip()
    if not description or description.lower() == "nan":
        raise ValueError("Missing description.")
    if len(description) > 255:
        raise ValueError("Description must be 255 characters or fewer.")

    raw_date = row.get("date")
    parsed_date = pd.to_datetime(raw_date, errors="coerce")
    if pd.isna(parsed_date):
        raise ValueError(f"Invalid or unparseable date: {raw_date!r}.")
    if parsed_date.date() > datetime.utcnow().date():
        raise ValueError("Date is in the future.")

    raw_amount = row.get("amount")
    try:
        amount = float(raw_amount)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid amount: {raw_amount!r}.")
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Amount must be a positive number.")
    if amount > 10_000_000:
        raise ValueError("Amount is unrealistically large.")

    raw_type = str(row.get("type", "")).strip().lower()
    if raw_type in ("expense", "debit", "exp"):
        txn_type = "expense"
    elif raw_type in ("income", "credit", "inc"):
        txn_type = "income"
    else:
        raise ValueError(f"Invalid transaction type: {raw_type!r} (expected 'income' or 'expense').")

    merchant_raw = row.get("merchant")
    merchant = str(merchant_raw).strip() if merchant_raw is not None and str(merchant_raw).strip().lower() != "nan" else description
    if len(merchant) > 255:
        raise ValueError("Merchant must be 255 characters or fewer.")

    return {
        "transaction_date": parsed_date.date(),
        "description": description,
        "merchant": merchant,
        "amount": round(amount, 2),
        "transaction_type": txn_type,
    }


def import_transactions(
    db: Session,
    user: User,
    file_bytes: bytes,
    filename: str,
    provider: LLMProvider | None,
    commit: bool = True,
) -> ImportResult:
    df = _validate_and_read(file_bytes, filename)
    result = ImportResult(total_rows=len(df))

    # Existing (date, description, amount) tuples for this user, used to skip
    # obvious duplicate re-imports (e.g. uploading the same file twice).
    existing_keys = {
        (t.transaction_date, t.description.strip().lower(), float(t.amount))
        for t in db.query(Transaction).filter(Transaction.user_id == user.id).all()
    }
    categories_by_name = {c.name: c for c in db.query(Category).all()}
    seen_in_file: set[tuple] = set()

    new_transactions: list[Transaction] = []

    for idx, row in df.iterrows():
        row_number = idx + 2  # +1 for 0-index, +1 for header row
        try:
            clean = _parse_row(row)
        except ValueError as exc:
            result.failed_count += 1
            if len(result.errors) < MAX_ERRORS_RETURNED:
                result.errors.append(RowError(row_number=row_number, reason=str(exc)))
            continue

        key = (clean["transaction_date"], clean["description"].strip().lower(), clean["amount"])
        if key in existing_keys or key in seen_in_file:
            result.duplicate_count += 1
            continue
        seen_in_file.add(key)

        categorization = categorize_transaction(
            provider,
            clean["description"],
            clean["merchant"],
            clean["amount"],
            clean["transaction_type"],
        )
        category = categories_by_name.get(categorization["category"])

        new_transactions.append(
            Transaction(
                user_id=user.id,
                transaction_date=clean["transaction_date"],
                description=clean["description"],
                merchant=clean["merchant"],
                amount=clean["amount"],
                transaction_type=TransactionType(clean["transaction_type"]),
                category_id=category.id if category else None,
                category_confidence=categorization["confidence"],
                category_source=categorization["source"],
                source=TransactionSource.CSV_UPLOAD,
            )
        )

        if new_transactions:
            db.add_all(new_transactions)

        # Obtain the IDs before committing.
        db.flush()
        result.transaction_ids = [
            str(transaction.id)
            for transaction in new_transactions
        ]

        if commit:
            db.commit()

    result.imported_count = len(new_transactions)
    return result