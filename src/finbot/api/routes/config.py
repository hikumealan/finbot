"""Live app configuration API."""
from fastapi import APIRouter, HTTPException

from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import ConfigUpdate
from finbot.config import settings
from finbot.llm.client import is_ollama_available

router = APIRouter(prefix="/api/config", tags=["config"])

_CONFIG_SCHEMA = {
    "llm": {
        "ollama_model": {"type": "text", "description": "Active LLM model"},
        "ollama_host": {"type": "text", "description": "Ollama API endpoint"},
    },
    "security": {
        "session_timeout_minutes": {"type": "slider", "min": 1, "max": 120, "description": "Auto-lock timeout (minutes)"},
        "require_pin": {"type": "toggle", "description": "Require PIN to access the app"},
    },
    "analysis": {
        "default_inflation_rate": {"type": "slider", "min": 0.01, "max": 0.10, "step": 0.005, "format": "percent", "description": "Default inflation rate"},
        "rebalance_drift_threshold": {"type": "slider", "min": 0.01, "max": 0.20, "step": 0.01, "format": "percent", "description": "Rebalance drift threshold"},
    },
    "alerts": {
        "emergency_fund_minimum_months": {"type": "slider", "min": 1, "max": 12, "description": "Emergency fund minimum (months)"},
        "data_staleness_warning_days": {"type": "slider", "min": 14, "max": 180, "description": "Data staleness warning (days)"},
        "savings_rate_target_pct": {"type": "slider", "min": 5, "max": 50, "description": "Savings rate target (%)"},
    },
    "import": {
        "import_cleanup_days": {"type": "slider", "min": 0, "max": 365, "description": "Import file cleanup (days, 0=never)"},
    },
    "display": {
        "currency": {"type": "select", "options": ["USD", "EUR", "GBP", "CAD", "AUD"], "description": "Currency symbol"},
        "date_format": {"type": "select", "options": ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"], "description": "Date format"},
        "dark_mode": {"type": "select", "options": ["light", "dark", "system"], "description": "Color theme"},
    },
}

_DEFAULTS = {
    "ollama_model": settings.ollama_model,
    "ollama_host": settings.ollama_host,
    "session_timeout_minutes": settings.session_timeout_minutes,
    "require_pin": settings.require_pin,
    "default_inflation_rate": settings.default_inflation_rate,
    "rebalance_drift_threshold": settings.rebalance_drift_threshold,
    "emergency_fund_minimum_months": 3,
    "data_staleness_warning_days": 60,
    "savings_rate_target_pct": 20,
    "import_cleanup_days": settings.import_cleanup_days,
    "currency": "USD",
    "date_format": "YYYY-MM-DD",
    "dark_mode": "system",
}


def _load_overrides(db) -> dict:


    try:
        result = db.execute(db.bind.dialect.has_table(db.bind, "user_config"))  # noqa: F841
    except Exception:
        pass

    overrides = {}
    try:
        rows = db.execute("SELECT section, key, value FROM user_config").fetchall()  # type: ignore[arg-type]
        for row in rows:
            overrides[row[1]] = row[2]
    except Exception:
        pass
    return overrides


@router.get("")
def get_config(db: DbSession, _user: CurrentUser):
    overrides = _load_overrides(db)
    result = {}
    for section, fields in _CONFIG_SCHEMA.items():
        result[section] = {}
        for key, meta in fields.items():
            val = overrides.get(key, _DEFAULTS.get(key))
            result[section][key] = {**meta, "value": val, "default": _DEFAULTS.get(key)}

    if is_ollama_available():
        import httpx

        try:
            r = httpx.get(f"{settings.ollama_host}/api/tags", timeout=3)
            models = [m["name"] for m in r.json().get("models", [])]
            result["llm"]["ollama_model"]["options"] = models
        except Exception:
            pass

    return result


@router.patch("")
def update_config(body: ConfigUpdate, db: DbSession, _user: CurrentUser):
    flat_keys = {}
    for fields in _CONFIG_SCHEMA.values():
        flat_keys.update(fields)

    if body.key not in flat_keys:
        raise HTTPException(status_code=400, detail=f"Unknown config key: {body.key}")

    try:
        from sqlalchemy import text

        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_config (
                id INTEGER PRIMARY KEY,
                section TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                UNIQUE(section, key)
            )
        """))
        db.execute(
            text("INSERT OR REPLACE INTO user_config (section, key, value) VALUES (:section, :key, :value)"),
            {"section": body.section, "key": body.key, "value": str(body.value)},
        )
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok", "key": body.key, "value": body.value}


@router.delete("")
def reset_config(db: DbSession, _user: CurrentUser, section: str | None = None):
    from sqlalchemy import text

    try:
        if section:
            db.execute(text("DELETE FROM user_config WHERE section = :section"), {"section": section})
        else:
            db.execute(text("DELETE FROM user_config"))
        db.commit()
    except Exception:
        pass
    return {"status": "reset"}
