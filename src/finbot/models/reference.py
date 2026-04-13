from __future__ import annotations

from sqlalchemy import Boolean, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from finbot.models.base import Base


class StateTaxRule(Base):
    __tablename__ = "state_tax_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    state_code: Mapped[str] = mapped_column(String(2), unique=True)
    has_income_tax: Mapped[bool] = mapped_column(Boolean)
    exempts_own_munis: Mapped[bool] = mapped_column(Boolean, default=True)
    exempts_all_munis: Mapped[bool] = mapped_column(Boolean, default=False)
    top_marginal_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class FederalTaxBracket(Base):
    __tablename__ = "federal_tax_brackets"
    __table_args__ = (
        UniqueConstraint("tax_year", "filing_status", "bracket_floor", name="uq_bracket"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tax_year: Mapped[int] = mapped_column(Integer)
    filing_status: Mapped[str] = mapped_column(String(30))
    bracket_floor: Mapped[float] = mapped_column(Numeric(12, 2))
    bracket_ceiling: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    rate: Mapped[float] = mapped_column(Numeric(5, 4))


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    pattern: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
