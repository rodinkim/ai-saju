"""
App-level settings loaded from environment (.env in this directory).

Import this module early (e.g. from main) so .env is applied before other reads.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parent
load_dotenv(_BACKEND_ROOT / ".env")

DEFAULT_LLM_MODEL = "claude-haiku-4-5-20251001"
LLM_MODEL_ENV = "SAJU_LLM_MODEL"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
BACKEND_PORT_ENV = "BACKEND_PORT"
DEFAULT_BACKEND_PORT = 8080


def _normalize_secret(value: str) -> str:
    """Normalize env secrets with mixed whitespace/newline encodings."""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    return normalized.replace("\\n", "\n")


def _read_env(key: str) -> str:
    raw = os.environ.get(key, "")
    if not isinstance(raw, str):
        return ""
    return _normalize_secret(raw)


def get_llm_model() -> str:
    v = _read_env(LLM_MODEL_ENV)
    return v or DEFAULT_LLM_MODEL


def get_anthropic_api_key() -> str:
    v = _read_env(ANTHROPIC_API_KEY_ENV)
    if not v:
        return ""
    # Anthropic keys are single-line; collapse accidental whitespace/newlines from Secret Manager or .env pastes
    return "".join(v.split())


def get_backend_port() -> int:
    v = _read_env(BACKEND_PORT_ENV)
    if not v:
        return DEFAULT_BACKEND_PORT
    try:
        return int(v)
    except ValueError:
        return DEFAULT_BACKEND_PORT
