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


def get_llm_model() -> str:
    v = os.environ.get(LLM_MODEL_ENV, "").strip()
    return v or DEFAULT_LLM_MODEL
