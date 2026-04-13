from __future__ import annotations

from sqlalchemy import Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from finbot.models.base import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("category", "effective_month", name="uq_budget_cat_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(100))
    monthly_limit: Mapped[float] = mapped_column(Numeric(10, 2))
    effective_month: Mapped[str] = mapped_column(String(7))  # YYYY-MM format
