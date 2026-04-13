from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from finbot.models.base import Base


class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    principal: Mapped[float] = mapped_column(Numeric(12, 2))
    interest_rate: Mapped[float] = mapped_column(Numeric(6, 4))
    minimum_payment: Mapped[float] = mapped_column(Numeric(10, 2))
    term_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    debt_type: Mapped[str] = mapped_column(String(50))  # mortgage/student/auto/credit_card
