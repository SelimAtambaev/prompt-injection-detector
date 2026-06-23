"""Application configuration.

Settings are read from environment variables (or a local .env file). Secrets
such as the OpenAI API key are NEVER hard-coded and NEVER logged.

The OpenAI key defaults to an empty string so that the package imports cleanly
in test/CI environments that have no key. The key is only required at the
moment a real completion is requested (see app/proxy/llm.py), which keeps the
block path and the test suite runnable without credentials.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # --- Risk thresholds (recalibrated for the Phase-4 weighted score; tunable) ---
    block_threshold: float = 0.70
    flag_threshold: float = 0.35
    risk_ml_weight: float = 1.0   # weight on the category-agnostic ML signal

    # --- Logging: "full" | "truncated" | "hashed" ---
    prompt_log_mode: str = "truncated"
    prompt_log_max_chars: int = 200

    # --- Persistence (Phase 5). SQLite by default (zero setup); set
    # DATABASE_URL to a postgresql+psycopg://... URL for production. ---
    database_url: str = "sqlite:///./firewall.db"
    persist_enabled: bool = True


settings = Settings()
