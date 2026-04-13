"""Statement and tax document parsers."""
from __future__ import annotations

from pathlib import Path

from finbot.parsers.base import BaseParser, ParseResult
from finbot.parsers.csv_parser import CsvParser
from finbot.parsers.ofx_parser import OfxParser
from finbot.parsers.pdf_parser import PdfParser

_PARSERS: list[BaseParser] = [CsvParser(), OfxParser(), PdfParser()]


def detect_and_parse(path: Path) -> ParseResult:
    """Auto-detect file type and parse it."""
    for parser in _PARSERS:
        if parser.can_parse(path):
            return parser.parse(path)

    result = ParseResult()
    result.warnings.append(f"No parser found for file type: {path.suffix}")
    return result
