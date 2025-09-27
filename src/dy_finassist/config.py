from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Allow optional python-dotenv usage without hard dependency
try:  # pragma: no cover - optional helper
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore

if load_dotenv:  # pragma: no cover - only executed when package is available
    load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REFERENCE_DATA_DIR = DATA_DIR / "reference"
RAW_DATA_DIR = DATA_DIR / "raw"
ASSETS_DIR = PROJECT_ROOT / "assets"
DOCS_DIR = PROJECT_ROOT / "docs"


@dataclass(slots=True)
class AppSettings:
    """Runtime configuration for the Streamlit applications."""

    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    youtube_api_key: Optional[str] = os.getenv("YOUTUBE_API_KEY")
    enable_voice_features: bool = os.getenv("ENABLE_VOICE_FEATURES", "false").lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings."""

    return AppSettings()


__all__ = [
    "AppSettings",
    "ASSETS_DIR",
    "DATA_DIR",
    "DOCS_DIR",
    "get_settings",
    "PROJECT_ROOT",
    "RAW_DATA_DIR",
    "REFERENCE_DATA_DIR",
]
