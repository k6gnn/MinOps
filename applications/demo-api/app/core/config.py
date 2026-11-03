from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEMO_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fault_simulation_enabled: bool = False
    # Bounded so a misconfigured value can't hold connections open indefinitely
    max_delay_seconds: int = Field(default=30, ge=0, le=300)


@lru_cache
def get_settings() -> Settings:
    return Settings()
