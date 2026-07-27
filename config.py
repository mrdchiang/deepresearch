"""
DeepResearch — configuration, error classes, session state.
All other modules import from here.
"""

import json, os, re, time, threading
from collections import deque
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

CONFIG = {
    "llm": {
        "api_key": os.getenv("OPENAI_API_KEY", os.getenv("DEEPRESEARCH_API_KEY", "***")),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("DEEPRESEARCH_MODEL", "gpt-4o"),
        "temperature": 0.3,
        "max_tokens": 4096,
    },
    "search": {
        "max_results": 5,
        "region": "wt-wt",
        "safesearch": "moderate",
        "timeout": 15,
    },
    "research": {
        "max_iterations": 3,
        "min_findings": 5,
        "max_sub_questions": 5,
    },
    "server": {
        "host": os.getenv("DEEPRESEARCH_HOST", "127.0.0.1"),
        "port": int(os.getenv("DEEPRESEARCH_PORT", "5000")),
        "debug": False,
        "cors_origins": [
            origin.strip()
            for origin in os.getenv(
                "DEEPRESEARCH_CORS_ORIGINS",
                "http://localhost:5000,http://127.0.0.1:5000,https://mrdchiang.github.io",
            ).split(",")
            if origin.strip()
        ],
    },
    "vault": {
        "path": os.getenv("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/Documents/Obsidian Vault")),
        "enabled": os.getenv("DEEPRESEARCH_VAULT_ENABLED", "true").lower() == "true",
    },
    "security": {
        "api_token": os.getenv("DEEPRESEARCH_API_TOKEN", ""),
        "max_depth": int(os.getenv("DEEPRESEARCH_MAX_DEPTH", "4")),
        "max_question_chars": int(os.getenv("DEEPRESEARCH_MAX_QUESTION_CHARS", "1000")),
        "session_ttl_seconds": int(os.getenv("DEEPRESEARCH_SESSION_TTL_SECONDS", "86400")),
        "max_sessions": int(os.getenv("DEEPRESEARCH_MAX_SESSIONS", "100")),
        "rate_limit_per_minute": int(os.getenv("DEEPRESEARCH_RATE_LIMIT_PER_MINUTE", "10")),
        "max_concurrent_research": int(os.getenv("DEEPRESEARCH_MAX_CONCURRENT", "5")),
        "request_timeout_seconds": int(os.getenv("DEEPRESEARCH_REQUEST_TIMEOUT", "600")),
        "active_session_timeout_seconds": int(os.getenv("DEEPRESEARCH_ACTIVE_TIMEOUT", "1800")),
    },
}

# ═══════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════

SESSION_LOCK = threading.RLock()
RATE_LIMITS: dict[str, deque] = {}
ACTIVE_RESEARCH_COUNT = 0
ACTIVE_RESEARCH_CONDITION = threading.Condition(SESSION_LOCK)


# ═══════════════════════════════════════════════════════════
# ERRORS
# ═══════════════════════════════════════════════════════════

class ExternalServiceError(RuntimeError):
    """Safe error for upstream API/search failures."""


def public_error(exc: Exception) -> str:
    """Return a client-safe error message without API keys or provider payloads."""
    if isinstance(exc, ExternalServiceError):
        return str(exc)
    if isinstance(exc, json.JSONDecodeError):
        return "The model returned malformed JSON. Please retry."
    return "Research failed. Check server logs for details."
