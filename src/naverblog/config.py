"""설정 관리."""

from __future__ import annotations

import os
from pathlib import Path


APP_DIR = Path.home() / ".naverblog"
DB_PATH = APP_DIR / "naverblog.db"
PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "presets"

REQUIRED_ENV_VARS = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "search": "TAVILY_API_KEY",
}

# 기본 API 키 (Streamlit Cloud 등 .env 없는 환경용)
_DEFAULT_KEYS = {
    "ANTHROPIC_API_KEY": "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",
    "GEMINI_API_KEY": "AIzaSyAJZb8iDAW8Uv_UcOWQbNA2ry7gbJfkZ5I",
}


def inject_default_keys() -> None:
    """환경변수에 키가 없으면 기본값 주입."""
    for key, value in _DEFAULT_KEYS.items():
        if not os.environ.get(key):
            os.environ[key] = value


def ensure_app_dir() -> Path:
    """~/.naverblog/ 디렉토리 생성."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    return APP_DIR


def check_api_key(provider: str) -> bool:
    """특정 프로바이더의 API 키가 설정되어 있는지 확인."""
    var_name = REQUIRED_ENV_VARS.get(provider, "")
    return bool(os.environ.get(var_name))


def get_available_providers() -> list[str]:
    """API 키가 설정된 프로바이더 목록 반환."""
    return [p for p in REQUIRED_ENV_VARS if check_api_key(p)]


def get_missing_keys() -> list[str]:
    """API 키가 누락된 프로바이더 목록 반환."""
    return [p for p in REQUIRED_ENV_VARS if not check_api_key(p)]
