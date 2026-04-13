from __future__ import annotations

import re

_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_ACCOUNT_NUM_RE = re.compile(r"\b(?:account|acct)[#:\s]*(\d{4,})\b", re.IGNORECASE)
_RAW_LONG_NUM_RE = re.compile(r"\b\d{10,}\b")
_EMAIL_RE = re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


def sanitize_for_llm(text: str, replacements: dict[str, str] | None = None) -> str:
    """Strip PII from text before sending to the local LLM.

    Replaces SSNs, account numbers, emails, and phone numbers with tokens.
    Accepts an optional ``replacements`` dict mapping raw values to tokens
    (e.g. ``{"John Doe": "[NAME_1]"}``).
    """
    if replacements:
        for raw, token in replacements.items():
            text = text.replace(raw, token)

    text = _SSN_RE.sub("[SSN_REDACTED]", text)
    text = _ACCOUNT_NUM_RE.sub("[ACCOUNT_REDACTED]", text)
    text = _EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    text = _PHONE_RE.sub("[PHONE_REDACTED]", text)
    text = _RAW_LONG_NUM_RE.sub("[NUM_REDACTED]", text)

    return text
