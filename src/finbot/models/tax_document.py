from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finbot.models.base import Base


class TaxDocument(Base):
    __tablename__ = "tax_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    tax_year: Mapped[int] = mapped_column(Integer)
    doc_type: Mapped[str] = mapped_column(String(30))  # W2/1040/1099_DIV/1099_INT/1099_B/K1/other
    source_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    line_items: Mapped[list[TaxLineItem]] = relationship(back_populates="document", cascade="all, delete-orphan")


class TaxLineItem(Base):
    __tablename__ = "tax_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    tax_document_id: Mapped[int] = mapped_column(ForeignKey("tax_documents.id"), index=True)
    field_key: Mapped[str] = mapped_column(String(50))  # e.g. "box_1", "line_22"
    field_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    value: Mapped[str] = mapped_column(Text)
    data_type: Mapped[str] = mapped_column(String(20), default="currency")  # currency/text/boolean

    document: Mapped[TaxDocument] = relationship(back_populates="line_items")
