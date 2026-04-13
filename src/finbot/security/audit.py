from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from finbot.models.audit_log import AuditLog


def _json_default(obj: Any) -> str:
    """Fallback serializer for types json.dumps can't handle."""
    return str(obj)


def create_audit_entry(
    session: Session,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=json.dumps(details, default=_json_default) if details else None,
    )
    session.add(entry)
    session.flush()
    return entry
