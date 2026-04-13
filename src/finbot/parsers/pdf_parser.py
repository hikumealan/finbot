"""PDF financial statement parser using pdfplumber."""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import pdfplumber

from finbot.parsers.base import BaseParser, ParsedTransaction, ParseResult

_DATE_PATTERNS = [
    re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"),
    re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2})"),
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),
    re.compile(r"(\w{3})\s+(\d{1,2}),?\s+(\d{4})"),
]

_AMOUNT_RE = re.compile(r"-?\$?\s*[\d,]+\.\d{2}")


class PdfParser(BaseParser):
    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> ParseResult:
        result = ParseResult()
        result.account_institution = "Unknown"

        try:
            with pdfplumber.open(path) as pdf:
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    all_text += text + "\n"

                    tables = page.extract_tables()
                    for table in tables:
                        self._parse_table(table, result)

                if not result.transactions:
                    self._parse_text_lines(all_text, result)

                self._detect_institution(all_text, result)

        except Exception as e:
            result.warnings.append(f"PDF parse error: {e}")

        if result.transactions:
            dates = [t.date for t in result.transactions]
            result.date_range = (min(dates), max(dates))

        return result

    def _parse_table(self, table: list[list[str | None]], result: ParseResult) -> None:
        if not table or len(table) < 2:
            return

        for row in table[1:]:
            if not row or len(row) < 3:
                continue

            cells = [str(c).strip() if c else "" for c in row]
            tx_date = self._extract_date(cells[0])
            if not tx_date:
                continue

            description = cells[1] if len(cells) > 1 else ""
            amount = self._extract_amount(cells)
            if amount is None:
                continue

            tx_type = "income" if amount > 0 else "expense"
            result.transactions.append(ParsedTransaction(
                date=tx_date,
                amount=amount,
                description=description.strip(),
                tx_type=tx_type,
            ))

    def _parse_text_lines(self, text: str, result: ParseResult) -> None:
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            tx_date = self._extract_date(line)
            if not tx_date:
                continue

            amounts = _AMOUNT_RE.findall(line)
            if not amounts:
                continue

            amount_str = amounts[-1].replace("$", "").replace(",", "").strip()
            try:
                amount = float(amount_str)
            except ValueError:
                continue

            desc = line
            for a in amounts:
                desc = desc.replace(a, "")
            for pattern in _DATE_PATTERNS:
                desc = pattern.sub("", desc)
            desc = re.sub(r"\s+", " ", desc).strip()

            if desc:
                tx_type = "income" if amount > 0 else "expense"
                result.transactions.append(ParsedTransaction(
                    date=tx_date,
                    amount=amount,
                    description=desc,
                    tx_type=tx_type,
                ))

    def _extract_date(self, text: str) -> date | None:
        for pattern in _DATE_PATTERNS:
            m = pattern.search(text)
            if not m:
                continue
            groups = m.groups()
            try:
                if len(groups[0]) == 4:
                    return date(int(groups[0]), int(groups[1]), int(groups[2]))
                if len(groups[2]) == 2:
                    year = 2000 + int(groups[2])
                    return date(year, int(groups[0]), int(groups[1]))
                if len(groups[2]) == 4:
                    if groups[0].isalpha():
                        dt = datetime.strptime(f"{groups[0]} {groups[1]} {groups[2]}", "%b %d %Y")
                        return dt.date()
                    return date(int(groups[2]), int(groups[0]), int(groups[1]))
            except (ValueError, IndexError):
                continue
        return None

    def _extract_amount(self, cells: list[str]) -> float | None:
        for cell in reversed(cells):
            amounts = _AMOUNT_RE.findall(cell)
            if amounts:
                try:
                    return float(amounts[-1].replace("$", "").replace(",", "").strip())
                except ValueError:
                    continue
        return None

    def _detect_institution(self, text: str, result: ParseResult) -> None:
        text_lower = text.lower()
        institutions = {
            "chase": "Chase",
            "bank of america": "Bank of America",
            "wells fargo": "Wells Fargo",
            "citi": "Citi",
            "capital one": "Capital One",
            "fidelity": "Fidelity",
            "vanguard": "Vanguard",
            "schwab": "Charles Schwab",
            "td ameritrade": "TD Ameritrade",
            "e*trade": "E*TRADE",
            "usaa": "USAA",
            "navy federal": "Navy Federal",
        }
        for keyword, name in institutions.items():
            if keyword in text_lower:
                result.account_institution = name
                return
