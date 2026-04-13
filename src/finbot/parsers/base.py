"""Abstract base interface for all financial statement parsers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class ParsedTransaction:
    date: date
    amount: float
    description: str
    category: str | None = None
    subcategory: str | None = None
    tx_type: str = "expense"  # expense/income/transfer


@dataclass
class ParsedHolding:
    symbol: str
    shares: float
    cost_basis: float
    current_price: float | None = None
    price_as_of: date | None = None
    asset_class: str = "other"


@dataclass
class ParseResult:
    transactions: list[ParsedTransaction] = field(default_factory=list)
    holdings: list[ParsedHolding] = field(default_factory=list)
    account_institution: str | None = None
    account_name: str | None = None
    account_type: str | None = None
    warnings: list[str] = field(default_factory=list)
    date_range: tuple[date, date] | None = None

    @property
    def total_debits(self) -> float:
        return sum(t.amount for t in self.transactions if t.amount < 0)

    @property
    def total_credits(self) -> float:
        return sum(t.amount for t in self.transactions if t.amount > 0)


class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """Return True if this parser can handle the given file."""

    @abstractmethod
    def parse(self, path: Path) -> ParseResult:
        """Parse the file and return structured results."""

    @staticmethod
    def detect_file_type(path: Path) -> str | None:
        """Detect file type by extension and content sniffing."""
        suffix = path.suffix.lower()
        type_map = {
            ".pdf": "pdf",
            ".csv": "csv",
            ".tsv": "csv",
            ".ofx": "ofx",
            ".qfx": "ofx",
        }
        return type_map.get(suffix)
