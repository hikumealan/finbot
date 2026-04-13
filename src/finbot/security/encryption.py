from __future__ import annotations

import os
import secrets

from finbot.config import settings


def get_or_create_key() -> str:
    settings.ensure_dirs()
    key_file = settings.key_file

    if key_file.exists():
        return key_file.read_text().strip()

    key = secrets.token_hex(32)
    key_file.write_text(key)
    if os.name != "nt":
        key_file.chmod(0o600)
    return key
