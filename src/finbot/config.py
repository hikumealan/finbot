from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _default_watch_folder() -> Path:
    return Path.home() / "finbot-inbox"


class Settings(BaseSettings):
    model_config = {"env_prefix": "FINBOT_", "env_file": ".env", "extra": "ignore"}

    # Ollama
    ollama_model: str = "mistral:7b-instruct-v0.3-q4_K_M"
    ollama_host: str = "http://127.0.0.1:11434"

    # Paths
    data_dir: Path = _default_data_dir()
    key_dir: Path = Path.home() / ".finbot"
    watch_folder: Path = _default_watch_folder()

    # Session security
    session_timeout_minutes: int = 15
    require_pin: bool = True

    # Projections
    default_inflation_rate: float = 0.03
    rebalance_drift_threshold: float = 0.05

    # Import cleanup
    import_cleanup_days: int = 30

    # LAN server
    lan_port: int = 8501

    @property
    def db_path(self) -> Path:
        return self.data_dir / "finbot.db"

    @property
    def imports_dir(self) -> Path:
        return self.data_dir / "imports"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    @property
    def key_file(self) -> Path:
        return self.key_dir / "key"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.imports_dir, self.backups_dir, self.key_dir):
            d.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            self.key_dir.chmod(0o700)


settings = Settings()
