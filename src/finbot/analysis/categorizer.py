"""Auto-categorize transactions based on description patterns."""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from finbot.models.reference import CategoryRule

_DEFAULT_RULES: list[tuple[str, str, str | None]] = [
    (r"(?i)walmart|target|costco|sam'?s club", "Shopping", "General"),
    (r"(?i)kroger|safeway|whole foods|trader joe|grocery|publix|aldi", "Groceries", None),
    (r"(?i)shell|chevron|exxon|bp|gas|fuel|speedway", "Transportation", "Gas"),
    (r"(?i)uber|lyft", "Transportation", "Rideshare"),
    (r"(?i)netflix|hulu|disney|spotify|apple music|youtube|hbo", "Entertainment", "Streaming"),
    (r"(?i)amazon", "Shopping", "Online"),
    (r"(?i)starbucks|mcdonald|chipotle|restaurant|cafe|diner|pizza|taco|burger", "Dining", None),
    (r"(?i)electric|water|gas bill|utility|power|sewer", "Utilities", None),
    (r"(?i)at&t|verizon|t-mobile|comcast|xfinity|spectrum|internet", "Utilities", "Telecom"),
    (r"(?i)rent|mortgage|hoa", "Housing", None),
    (r"(?i)insurance|geico|allstate|progressive|state farm", "Insurance", None),
    (r"(?i)doctor|hospital|pharmacy|cvs|walgreens|medical|dental|health", "Healthcare", None),
    (r"(?i)gym|fitness|planet fitness|peloton", "Health", "Fitness"),
    (r"(?i)payroll|direct deposit|salary|wage", "Income", "Salary"),
    (r"(?i)dividend|interest income|interest paid", "Income", "Investment"),
    (r"(?i)transfer|xfer|zelle|venmo|paypal", "Transfer", None),
]


def categorize_description(description: str, session: Session | None = None) -> tuple[str | None, str | None]:
    """Return (category, subcategory) for a transaction description."""
    if session:
        rules = session.query(CategoryRule).order_by(CategoryRule.priority.desc()).all()
        for rule in rules:
            if re.search(rule.pattern, description, re.IGNORECASE):
                return rule.category, rule.subcategory

    for pattern, category, subcategory in _DEFAULT_RULES:
        if re.search(pattern, description):
            return category, subcategory

    return None, None
