from __future__ import annotations

import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    trampoline_width_m: float = Field(default=4.28)
    trampoline_length_m: float = Field(default=2.14)
    jump_height_threshold_m: float = Field(default=0.15)
    vertical_height_scale_m: float = Field(default=1.0)
    live_recalibration_confidence_threshold: float = Field(default=0.4)
    default_fps: float = Field(default=30.0)
    max_frames_debug_save: int = Field(default=200)
    debug_output_dir: str = Field(default="/tmp/jumptek-debug")
    # Comma-separated list of allowed CORS origins.
    # Set CORS_ORIGINS env var in production, e.g. "https://your-app.lovable.app"
    cors_origins: list[str] = Field(
        default_factory=lambda: os.environ.get("CORS_ORIGINS", "*").split(",")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
