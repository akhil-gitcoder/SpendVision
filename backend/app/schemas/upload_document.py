import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from app.schemas.transaction import UploadRowError


class UploadDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    month: str
    filename: str
    size_bytes: int
    total_rows: int
    imported_count: int
    duplicate_count: int
    failed_count: int
    uploaded_at: datetime


class SavedUpload(UploadDocumentOut):
    errors: list[UploadRowError]


class UploadPreview(BaseModel):
    document: SavedUpload
    columns: list[str]
    rows: list[list[str]]
    has_more: bool