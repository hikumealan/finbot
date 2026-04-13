"""Document type and data classification engine."""
from __future__ import annotations

from finbot.parsers.base import ParseResult

_INSTITUTIONS = {
    "chase": "Chase", "bank of america": "Bank of America", "wells fargo": "Wells Fargo",
    "citi": "Citi", "capital one": "Capital One", "fidelity": "Fidelity",
    "vanguard": "Vanguard", "schwab": "Charles Schwab", "td ameritrade": "TD Ameritrade",
    "e*trade": "E*TRADE", "usaa": "USAA", "navy federal": "Navy Federal",
    "ally": "Ally Bank", "discover": "Discover", "american express": "American Express",
    "amex": "American Express", "barclays": "Barclays", "goldman sachs": "Goldman Sachs",
    "morgan stanley": "Morgan Stanley", "merrill": "Merrill Lynch",
    "robinhood": "Robinhood", "coinbase": "Coinbase", "sofi": "SoFi",
    "pnc": "PNC", "us bank": "US Bank", "regions": "Regions",
    "suntrust": "SunTrust", "truist": "Truist", "fifth third": "Fifth Third",
    "citizens": "Citizens Bank", "td bank": "TD Bank",
}


def classify(result: ParseResult) -> dict:
    """Classify a parsed result and return classification metadata."""
    doc_type = _infer_document_type(result)
    institution = result.account_institution
    confidence = 1.0 if institution and institution != "Unknown" else 0.0
    tags = _compute_tags(result)
    cat_summary = _categorization_summary(result)

    return {
        "document_type": doc_type,
        "institution": institution,
        "institution_confidence": confidence,
        "data_classifications": tags,
        "category_summary": cat_summary,
    }


def detect_institution(text: str) -> tuple[str | None, float]:
    """Detect institution from text. Returns (name, confidence)."""
    text_lower = text.lower()
    for keyword, name in _INSTITUTIONS.items():
        if keyword in text_lower:
            return name, 1.0
    return None, 0.0


def _infer_document_type(result: ParseResult) -> str:
    if result.holdings:
        return "brokerage_statement"

    txs = result.transactions
    if not txs:
        return "unknown"

    neg_count = sum(1 for t in txs if t.amount < 0)
    pos_count = sum(1 for t in txs if t.amount > 0)

    if neg_count > 0 and pos_count == 0:
        return "credit_card_statement"

    has_large_deposit = any(t.amount > 1000 for t in txs if t.amount > 0)
    if has_large_deposit and neg_count > pos_count:
        return "checking_statement"

    if pos_count > neg_count and not has_large_deposit:
        return "savings_statement"

    return "checking_statement"


def _compute_tags(result: ParseResult) -> list[str]:
    tags = []
    for t in result.transactions:
        desc = t.description.lower()
        if any(kw in desc for kw in ("payroll", "direct deposit", "salary", "wage")):
            if "contains_income" not in tags:
                tags.append("contains_income")
        if any(kw in desc for kw in ("transfer", "xfer", "zelle", "venmo")):
            if "contains_transfers" not in tags:
                tags.append("contains_transfers")
        if abs(t.amount) > 5000:
            if "high_value" not in tags:
                tags.append("high_value")
    return tags


def _categorization_summary(result: ParseResult) -> dict[str, int]:
    categorized = sum(1 for t in result.transactions if t.category)
    total = len(result.transactions)
    return {
        "categorized": categorized,
        "uncategorized": total - categorized,
        "total": total,
    }
