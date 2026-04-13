from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finbot.models.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    account_type: Mapped[str] = mapped_column(String(50))  # checking/savings/brokerage/retirement/credit
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    is_tax_advantaged: Mapped[bool] = mapped_column(Boolean, default=False)

    transactions: Mapped[list[Transaction]] = relationship(back_populates="account")  # noqa: F821
    holdings: Mapped[list[Holding]] = relationship(back_populates="account")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Account {self.institution} - {self.name} ({self.account_type})>"
