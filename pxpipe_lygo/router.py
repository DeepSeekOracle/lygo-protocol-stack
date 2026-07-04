"""Multi-provider availability (routing metadata only; proxy forwards upstream)."""

from __future__ import annotations

import os

from pxpipe_lygo.config import PROVIDER_ORDER


def provider_available(name: str) -> bool:
    keys = {
        "grok": ("XAI_API_KEY", "GROK_API_KEY"),
        "claude": ("ANTHROPIC_API_KEY",),
        "gemini": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        "openai": ("OPENAI_API_KEY",),
    }
    for env in keys.get(name, ()):
        if os.environ.get(env, "").strip():
            return True
    return False


def select_provider(preferred: str | None = None) -> str:
    if preferred and provider_available(preferred):
        return preferred
    for name in PROVIDER_ORDER:
        if provider_available(name):
            return name
    return "pass_through"


def upstream_base_url(provider: str) -> str | None:
    bases = {
        "claude": "https://api.anthropic.com",
        "openai": "https://api.openai.com",
        "grok": "https://api.x.ai",
        "gemini": "https://generativelanguage.googleapis.com",
    }
    return bases.get(provider)