from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finbot.models.base import Base


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    goal_type: Mapped[str] = mapped_column(String(50))  # retirement/emergency_fund/house/college/custom
    target_amount: Mapped[float] = mapped_column(Numeric(14, 2))
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    linked_account_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated IDs
    current_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
