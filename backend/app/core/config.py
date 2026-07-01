"""Application configuration, loaded from environment / .env file.

Design note: the app is intentionally runnable with zero credentials. When
CWA_API_KEY is absent the app falls back to MOCK mode so the full request path
(adapter -> normalization -> API response -> frontend) works before any key
exists. This keeps the deliverable self-contained and demoable at every step.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # External credentials (all optional; empty => degraded/mock behaviour).
    cwa_api_key: str = ""
    tdx_client_id: str = ""
    tdx_client_secret: str = ""
    gemini_api_key: str = ""

    # Behaviour tuning.
    cache_ttl_seconds: int = 1800
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Upstream host (canonical is cwa.gov.tw; the legacy cwb.gov.tw is retired).
    cwa_base_url: str = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
    upstream_timeout_seconds: float = 10.0

    @property
    def use_mock(self) -> bool:
        """Serve fixture data whenever the CWA key is not configured."""
        return not self.cwa_api_key.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
