from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from finbot.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state_of_residence: Mapped[str | None] = mapped_column(String(2), nullable=True)
    risk_tolerance: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    retirement_target_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filing_status: Mapped[str | None] = mapped_column(String(30), nullable=True)  # single/married_joint/married_separate/head_of_household
    employer_match_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pin_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
