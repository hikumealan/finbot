"""Tax document parser for W2, 1040, 1099, and K-1 forms."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber


@dataclass
class TaxParseResult:
    doc_type: str  # W2/1040/1099_DIV/1099_INT/1099_B/K1/other
    tax_year: int | None = None
    fields: dict[str, str] = field(default_factory=dict)
    raw_text: str = ""
    warnings: list[str] = field(default_factory=list)
    confidence: float = 1.0


_FORM_MARKERS = {
    "W2": ["Form W-2", "Wage and Tax Statement", "W-2"],
    "1040": ["Form 1040", "U.S. Individual Income Tax Return"],
    "1099_DIV": ["Form 1099-DIV", "Dividends and Distributions"],
    "1099_INT": ["Form 1099-INT", "Interest Income"],
    "1099_B": ["Form 1099-B", "Proceeds From Broker"],
    "K1": ["Schedule K-1", "Partner's Share"],
}

_W2_FIELDS = {
    "box_1": r"(?:Box\s*1|Wages,?\s*tips).*?(\$?[\d,]+\.?\d*)",
    "box_2": r"(?:Box\s*2|Federal\s*income\s*tax\s*withheld).*?(\$?[\d,]+\.?\d*)",
    "box_3": r"(?:Box\s*3|Social\s*security\s*wages).*?(\$?[\d,]+\.?\d*)",
    "box_4": r"(?:Box\s*4|Social\s*security\s*tax\s*withheld).*?(\$?[\d,]+\.?\d*)",
    "box_5": r"(?:Box\s*5|Medicare\s*wages).*?(\$?[\d,]+\.?\d*)",
    "box_6": r"(?:Box\s*6|Medicare\s*tax\s*withheld).*?(\$?[\d,]+\.?\d*)",
}

_1040_FIELDS = {
    "line_1": r"(?:Line\s*1\b|Total\s*income).*?(\$?[\d,]+\.?\d*)",
    "line_11": r"(?:Line\s*11|Adjusted\s*gross\s*income).*?(\$?[\d,]+\.?\d*)",
    "line_15": r"(?:Line\s*15|Taxable\s*income).*?(\$?[\d,]+\.?\d*)",
    "line_24": r"(?:Line\s*24|Total\s*tax).*?(\$?[\d,]+\.?\d*)",
}

_YEAR_RE = re.compile(r"\b(20\d{2})\b")


def detect_form_type(text: str) -> str:
    for doc_type, markers in _FORM_MARKERS.items():
        for marker in markers:
            if marker.lower() in text.lower():
                return doc_type
    return "other"


def extract_tax_year(text: str) -> int | None:
    matches = _YEAR_RE.findall(text[:2000])
    years = [int(y) for y in matches if 2000 <= int(y) <= 2030]
    return max(years) if years else None


class TaxDocParser:
    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> TaxParseResult:
        try:
            with pdfplumber.open(path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
        except Exception as e:
            return TaxParseResult(
                doc_type="other",
                raw_text="",
                warnings=[f"Failed to read PDF: {e}"],
                confidence=0.0,
            )

        doc_type = detect_form_type(full_text)
        tax_year = extract_tax_year(full_text)

        field_patterns = {}
        if doc_type == "W2":
            field_patterns = _W2_FIELDS
        elif doc_type == "1040":
            field_patterns = _1040_FIELDS

        fields: dict[str, str] = {}
        for key, pattern in field_patterns.items():
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                value = m.group(1).replace("$", "").replace(",", "").strip()
                fields[key] = value

        confidence = 1.0 if doc_type != "other" else 0.3
        if doc_type != "other" and len(fields) < 2:
            confidence = 0.5

        warnings = []
        if doc_type == "other":
            warnings.append("Could not identify form type; stored as raw text")

        return TaxParseResult(
            doc_type=doc_type,
            tax_year=tax_year,
            fields=fields,
            raw_text=full_text,
            warnings=warnings,
            confidence=confidence,
        )
