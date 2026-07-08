"""ollama_client.py — thin wrapper around the local Ollama HTTP API.

Uses only the standard library (urllib) so there's nothing extra to
install. Requires `ollama serve` running locally (default: 127.0.0.1:11434).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_HOST = "http://127.0.0.1:11434"


class OllamaError(RuntimeError):
    pass


def _post(host: str, path: str, payload: dict, timeout: int = 120) -> dict:
    url = f"{host.rstrip('/')}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise OllamaError(
            f"Could not reach Ollama at {host}{path} — is `ollama serve` running? ({e})"
        ) from e


def generate(model: str, prompt: str, host: str = DEFAULT_HOST, timeout: int = 120) -> str:
    """One-shot generation. Returns the response text."""
    result = _post(host, "/api/generate", {"model": model, "prompt": prompt, "stream": False}, timeout)
    if "error" in result:
        raise OllamaError(f"Ollama error from model '{model}': {result['error']}")
    return result.get("response", "")


def embed(model: str, text: str, host: str = DEFAULT_HOST, timeout: int = 60) -> list[float]:
    """Returns an embedding vector for the given text.
    Recommended model: nomic-embed-text (`ollama pull nomic-embed-text`)."""
    result = _post(host, "/api/embeddings", {"model": model, "prompt": text}, timeout)
    if "error" in result:
        raise OllamaError(f"Ollama embedding error from model '{model}': {result['error']}")
    vec = result.get("embedding")
    if not vec:
        raise OllamaError(f"No embedding returned for model '{model}' — is it pulled?")
    return vec


def list_models(host: str = DEFAULT_HOST) -> list[str]:
    result = _post_get(host, "/api/tags")
    return [m["name"] for m in result.get("models", [])]


def _post_get(host: str, path: str) -> dict:
    url = f"{host.rstrip('/')}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise OllamaError(f"Could not reach Ollama at {url} ({e})") from e
