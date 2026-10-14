import uuid

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UploadImport(Base):
    """Records exactly which transactions an upload created."""

    __tablename__ = "upload_imports"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("upload_documents.id", ondelete="CASCADE"),
        primary_key=True,
    )

    transaction_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )