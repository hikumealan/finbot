from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finbot.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tx_type: Mapped[str] = mapped_column(String(20), default="expense")  # expense/income/transfer
    transfer_link_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    source_file: Mapped[str | None] = mapped_column(String(500), nullable=True)

    account: Mapped[Account] = relationship(back_populates="transactions")  # noqa: F821
    transfer_pair: Mapped[Transaction | None] = relationship(remote_side="Transaction.id")

    def __repr__(self) -> str:
        return f"<Transaction {self.date} {self.amount} {self.description[:30]}>"
