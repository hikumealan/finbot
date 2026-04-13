"""OFX/QFX financial statement parser."""
from __future__ import annotations

from pathlib import Path

from ofxparse import OfxParser as OfxLib

from finbot.parsers.base import (
    BaseParser,
    ParsedHolding,
    ParsedTransaction,
    ParseResult,
)


class OfxParser(BaseParser):
    def can_parse(self, path: Path) -> bool:
        return path.suffix.lower() in (".ofx", ".qfx")

    def parse(self, path: Path) -> ParseResult:
        result = ParseResult()

        try:
            with open(path, "rb") as f:
                ofx = OfxLib.parse(f)

            if ofx.account:
                acct = ofx.account
                result.account_institution = getattr(acct, "institution", None) and acct.institution.organization or "Unknown"
                result.account_name = getattr(acct, "account_id", None) or "OFX Account"
                acct_type = getattr(acct, "account_type", "") or ""
                result.account_type = self._map_account_type(str(acct_type))

                if hasattr(acct, "statement") and acct.statement:
                    for tx in acct.statement.transactions:
                        amount = float(tx.amount)
                        tx_type = "income" if amount > 0 else "expense"
                        result.transactions.append(ParsedTransaction(
                            date=tx.date.date() if hasattr(tx.date, "date") else tx.date,
                            amount=amount,
                            description=getattr(tx, "payee", "") or getattr(tx, "memo", "") or "",
                            tx_type=tx_type,
                        ))

            if hasattr(ofx, "account") and hasattr(ofx.account, "statement"):
                stmt = ofx.account.statement
                if hasattr(stmt, "positions"):
                    for pos in stmt.positions:
                        units = float(getattr(pos, "units", 0))
                        unit_price = float(getattr(pos, "unit_price", 0))
                        market_value = unit_price * units
                        result.holdings.append(ParsedHolding(
                            symbol=getattr(pos, "security", "") or "",
                            shares=units,
                            cost_basis=market_value,
                            current_price=unit_price,
                        ))
                        result.warnings.append(
                            f"Position {getattr(pos, 'security', '?')}: cost basis set to "
                            f"market value (${market_value:,.2f}) — OFX does not provide "
                            f"original cost basis. Update manually if needed."
                        )

        except Exception as e:
            result.warnings.append(f"OFX parse error: {e}")

        if result.transactions:
            dates = [t.date for t in result.transactions]
            result.date_range = (min(dates), max(dates))

        return result

    def _map_account_type(self, ofx_type: str) -> str:
        mapping = {
            "checking": "checking",
            "savings": "savings",
            "creditcard": "credit",
            "investment": "brokerage",
            "moneymrkt": "savings",
        }
        return mapping.get(ofx_type.lower(), "checking")
