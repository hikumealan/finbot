from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finbot.models.base import Base


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    shares: Mapped[float] = mapped_column(Numeric(14, 6))
    cost_basis: Mapped[float] = mapped_column(Numeric(12, 2))
    current_price: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    price_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    date: Mapped[date] = mapped_column(Date)
    asset_class: Mapped[str] = mapped_column(String(30), default="other")  # equity/bond/muni_bond/reit/cash/other

    account: Mapped[Account] = relationship(back_populates="holdings")  # noqa: F821
    muni_detail: Mapped[MuniBondDetail | None] = relationship(back_populates="holding", uselist=False)

    def __repr__(self) -> str:
        return f"<Holding {self.symbol} x{self.shares}>"


class MuniBondDetail(Base):
    __tablename__ = "muni_bond_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    holding_id: Mapped[int] = mapped_column(ForeignKey("holdings.id"), unique=True)
    issuer_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    coupon_rate: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credit_rating: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_amt_subject: Mapped[bool] = mapped_column(Boolean, default=False)
    is_callable: Mapped[bool] = mapped_column(Boolean, default=False)
    call_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bond_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # GO/revenue
    par_value: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    holding: Mapped[Holding] = relationship(back_populates="muni_detail")
