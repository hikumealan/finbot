from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from finbot.models.base import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    total_assets: Mapped[float] = mapped_column(Numeric(14, 2))
    total_liabilities: Mapped[float] = mapped_column(Numeric(14, 2))
    net_worth: Mapped[float] = mapped_column(Numeric(14, 2))
