"""CSV financial statement parser with institution profile detection."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from finbot.parsers.base import BaseParser, ParsedTransaction, ParseResult

_COLUMN_PROFILES: list[dict] = [
    {
        "name": "Chase",
        "date_cols": ["Transaction Date", "Posting Date"],
        "amount_col": "Amount",
        "desc_col": "Description",
        "type_col": "Type",
    },
    {
        "name": "Bank of America",
        "date_cols": ["Date"],
        "amount_col": "Amount",
        "desc_col": "Payee",
    },
    {
        "name": "Capital One",
        "date_cols": ["Transaction Date", "Posted Date"],
        "amount_col": "Amount",
        "desc_col": "Description",
        "debit_col": "Debit",
        "credit_col": "Credit",
    },
]

_DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%m-%d-%Y", "%d/%m/%Y"]


class CsvParser(BaseParser):
    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in (".csv", ".tsv")

    def parse(self, path: Path) -> ParseResult:
        result = ParseResult()

        try:
            sep = "\t" if path.suffix.lower() == ".tsv" else ","
            df = pd.read_csv(path, sep=sep, dtype=str)
            df.columns = df.columns.str.strip()

            profile = self._detect_profile(df)
            if profile:
                result.account_institution = profile["name"]
                self._parse_with_profile(df, profile, result)
            else:
                self._parse_generic(df, result)

        except Exception as e:
            result.warnings.append(f"CSV parse error: {e}")

        if result.transactions:
            dates = [t.date for t in result.transactions]
            result.date_range = (min(dates), max(dates))

        return result

    def _detect_profile(self, df: pd.DataFrame) -> dict | None:
        cols = set(df.columns)
        for profile in _COLUMN_PROFILES:
            date_cols = profile["date_cols"]
            if any(dc in cols for dc in date_cols):
                amount_key = profile.get("amount_col", "")
                desc_key = profile.get("desc_col", "")
                has_debit_credit = profile.get("debit_col") in cols or profile.get("credit_col") in cols
                if amount_key in cols or has_debit_credit:
                    if desc_key in cols:
                        return profile
        return None

    def _parse_with_profile(self, df: pd.DataFrame, profile: dict, result: ParseResult) -> None:
        date_col = next((c for c in profile["date_cols"] if c in df.columns), None)
        if not date_col:
            return

        desc_col = profile.get("desc_col", "")
        amount_col = profile.get("amount_col")

        for _, row in df.iterrows():
            tx_date = self._parse_date(str(row.get(date_col, "")))
            if not tx_date:
                continue

            description = str(row.get(desc_col, "")).strip()

            if amount_col and amount_col in df.columns:
                amount = self._parse_amount(str(row.get(amount_col, "0")))
            else:
                debit = self._parse_amount(str(row.get(profile.get("debit_col", ""), "0")))
                credit = self._parse_amount(str(row.get(profile.get("credit_col", ""), "0")))
                amount = credit - debit if credit else -debit

            if amount is None:
                continue

            tx_type = "income" if amount > 0 else "expense"
            result.transactions.append(ParsedTransaction(
                date=tx_date,
                amount=amount,
                description=description,
                tx_type=tx_type,
            ))

    def _parse_generic(self, df: pd.DataFrame, result: ParseResult) -> None:
        """Fall back to heuristic column detection."""
        cols_lower = {c.lower().strip(): c for c in df.columns}

        date_col = None
        for candidate in ("date", "transaction date", "posting date", "trans date"):
            if candidate in cols_lower:
                date_col = cols_lower[candidate]
                break

        amount_col = None
        for candidate in ("amount", "transaction amount", "value"):
            if candidate in cols_lower:
                amount_col = cols_lower[candidate]
                break

        desc_col = None
        for candidate in ("description", "payee", "memo", "details", "name"):
            if candidate in cols_lower:
                desc_col = cols_lower[candidate]
                break

        if not date_col or not amount_col:
            result.warnings.append("Could not detect date or amount columns")
            return

        for _, row in df.iterrows():
            tx_date = self._parse_date(str(row.get(date_col, "")))
            if not tx_date:
                continue

            amount = self._parse_amount(str(row.get(amount_col, "0")))
            if amount is None:
                continue

            description = str(row.get(desc_col, "")).strip() if desc_col else ""
            tx_type = "income" if amount > 0 else "expense"

            result.transactions.append(ParsedTransaction(
                date=tx_date,
                amount=amount,
                description=description,
                tx_type=tx_type,
            ))

    def _parse_date(self, text: str) -> date | None:
        text = text.strip()
        if not text or text.lower() == "nan":
            return None
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_amount(self, text: str) -> float | None:
        text = text.strip().replace("$", "").replace(",", "")
        if not text or text.lower() == "nan":
            return None
        text = text.replace("(", "-").replace(")", "")
        try:
            return float(text)
        except ValueError:
            return None
