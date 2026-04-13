"""Transaction fingerprinting and deduplication."""
from __future__ import annotations

import hashlib
import re
from datetime import date

from Levenshtein import ratio as lev_ratio
from sqlalchemy.orm import Session

from finbot.models.transaction import Transaction
from finbot.parsers.base import ParsedTransaction

_STRIP_RE = re.compile(r"[#:\-\s]+\d{4,}$")


def normalize_description(desc: str) -> str:
    desc = desc.lower().strip()
    desc = _STRIP_RE.sub("", desc)
    desc = re.sub(r"\s+", " ", desc)
    return desc


def compute_fingerprint(account_id: int, tx_date: date, amount: float, description: str) -> str:
    normalized = normalize_description(description)
    raw = f"{account_id}|{tx_date.isoformat()}|{amount:.2f}|{normalized}"
    return hashlib.sha256(raw.encode()).hexdigest()


def find_duplicates(
    session: Session,
    account_id: int,
    parsed_transactions: list[ParsedTransaction],
) -> tuple[list[ParsedTransaction], list[ParsedTransaction]]:
    """Split transactions into new and duplicate lists.

    Returns (new_transactions, duplicate_transactions).
    """
    new = []
    dupes = []

    existing_hashes: set[str] = set()
    all_existing = session.query(Transaction.fingerprint_hash).filter(
        Transaction.account_id == account_id,
        Transaction.fingerprint_hash.isnot(None),
    ).all()
    existing_hashes = {h[0] for h in all_existing}

    for tx in parsed_transactions:
        fp = compute_fingerprint(account_id, tx.date, tx.amount, tx.description)
        if fp in existing_hashes:
            dupes.append(tx)
        else:
            existing_hashes.add(fp)
            new.append(tx)

    return new, dupes


def find_fuzzy_matches(
    session: Session,
    account_id: int,
    transaction: ParsedTransaction,
    threshold: float = 0.85,
) -> list[Transaction]:
    """Find existing transactions that are fuzzy matches for a new one."""
    candidates = session.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.date == transaction.date,
        Transaction.amount == transaction.amount,
    ).all()

    matches = []
    norm_desc = normalize_description(transaction.description)
    for existing in candidates:
        existing_norm = normalize_description(existing.description)
        if lev_ratio(norm_desc, existing_norm) >= threshold:
            matches.append(existing)

    return matches


def detect_transfers(session: Session) -> int:
    """Link matching debit/credit pairs across different accounts as transfers.

    Returns the number of pairs linked.
    """
    unlinked = session.query(Transaction).filter(
        Transaction.transfer_link_id.is_(None),
        Transaction.tx_type != "transfer",
    ).all()

    by_date: dict[date, list[Transaction]] = {}
    for tx in unlinked:
        by_date.setdefault(tx.date, []).append(tx)

    linked_count = 0
    already_linked: set[int] = set()

    for tx_date, txs in by_date.items():
        for i, tx_a in enumerate(txs):
            if tx_a.id in already_linked:
                continue
            for tx_b in txs[i + 1:]:
                if tx_b.id in already_linked:
                    continue
                if tx_a.account_id == tx_b.account_id:
                    continue
                if abs(tx_a.amount + tx_b.amount) < 0.01:
                    tx_a.transfer_link_id = tx_b.id
                    tx_b.transfer_link_id = tx_a.id
                    tx_a.tx_type = "transfer"
                    tx_b.tx_type = "transfer"
                    already_linked.add(tx_a.id)
                    already_linked.add(tx_b.id)
                    linked_count += 1

    session.flush()
    return linked_count
