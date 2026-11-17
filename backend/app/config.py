"""Application settings, loaded from environment variables."""

import tempfile
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BACKEND_")

    app_name: str = "MIDI Analysis Backend"
    version: str = "0.1.0"
    environment: str = "development"
    max_upload_mb: float = 10.0
    video_dir: str = str(Path(tempfile.gettempdir()) / "midi-analysis-videos")
    video_max_age_minutes: float = 60.0  # rendered videos are deleted afterwards


@lru_cache
def get_settings() -> Settings:
    return Settings()
