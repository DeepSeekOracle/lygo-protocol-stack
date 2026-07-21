#!/usr/bin/env python3
"""OpenAI-compatible FastAPI for LYGO Qwen uncensored GGUF (OpenClaw plug-in)."""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from huggingface_hub import hf_hub_download
from pydantic import BaseModel, Field

APP_NAME = "lygo-qwen-uncensored"
MODEL_ALIAS = os.environ.get("MODEL_ALIAS", "lygo-qwen-uncensored")
HF_MODEL_ID = os.environ.get(
    "HF_MODEL_ID",
    "HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive",
)
HF_GGUF_FILE = os.environ.get(
    "HF_GGUF_FILE",
    "Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-Q4_K_M.gguf",
)
N_CTX = int(os.environ.get("N_CTX", "8192"))
N_GPU_LAYERS = int(os.environ.get("N_GPU_LAYERS", "-1"))
LYGO_API_SECRET = os.environ.get("LYGO_API_SECRET", "").strip()
MODEL_DIR = os.environ.get("MODEL_DIR", "/data/models")

app = FastAPI(title="LYGO Qwen Uncensored API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_llm = None
_load_error: str | None = None
_model_path: str | None = None


def _auth(
    authorization: Optional[str] = Header(default=None),
    x_lygo_key: Optional[str] = Header(default=None, alias="X-LYGO-Key"),
) -> None:
    """OpenClaw plug-in: Authorization: Bearer <HF_TOKEN>. Optional LYGO_API_SECRET gate."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            401,
            "Missing API key. Use Authorization: Bearer <HF_TOKEN> (or ollama for local).",
        )
    token = authorization[7:].strip()
    if len(token) < 8:
        raise HTTPException(401, "API key too short")
    if LYGO_API_SECRET:
        if (x_lygo_key or "").strip() != LYGO_API_SECRET and token != LYGO_API_SECRET:
            raise HTTPException(401, "Invalid X-LYGO-Key / secret")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = MODEL_ALIAS
    messages: list[ChatMessage]
    temperature: float = 0.85
    max_tokens: int = Field(default=512, ge=1, le=8192)
    top_p: float = 0.95
    stream: bool = False


def ensure_model() -> str:
    global _model_path, _load_error
    if _model_path and os.path.isfile(_model_path):
        return _model_path
    os.makedirs(MODEL_DIR, exist_ok=True)
    try:
        path = hf_hub_download(
            repo_id=HF_MODEL_ID,
            filename=HF_GGUF_FILE,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False,
        )
        _model_path = path
        return path
    except Exception as e:
        _load_error = str(e)
        raise


def get_llm():
    global _llm, _load_error
    if _llm is not None:
        return _llm
    try:
        from llama_cpp import Llama

        path = ensure_model()
        _llm = Llama(
            model_path=path,
            n_ctx=N_CTX,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
            chat_format="chatml",
        )
        return _llm
    except Exception as e:
        _load_error = str(e)
        raise HTTPException(
            503,
            f"Model not ready: {e}. Need GPU Space (L4/A10G) and first-boot download of ~21GB GGUF.",
        )


@app.on_event("startup")
def _warmup() -> None:
    # Best-effort download on boot (may take minutes)
    try:
        ensure_model()
    except Exception as e:
        print("[LYGO] warmup download deferred:", e)


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": APP_NAME,
        "docs": "/docs",
        "health": "/health",
        "openai": "/v1/chat/completions",
        "model": MODEL_ALIAS,
        "source": f"{HF_MODEL_ID}/{HF_GGUF_FILE}",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    ready = _llm is not None or (
        _model_path is not None and os.path.isfile(_model_path or "")
    )
    return {
        "ok": True,
        "model_loaded": _llm is not None,
        "gguf_present": bool(_model_path and os.path.isfile(_model_path)),
        "model_path": _model_path,
        "error": _load_error,
        "gpu_layers": N_GPU_LAYERS,
        "alias": MODEL_ALIAS,
    }


@app.get("/v1/models")
def list_models(_: None = Depends(_auth)) -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ALIAS,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "DeepSeekOracle",
            }
        ],
    }


@app.post("/v1/chat/completions")
def chat_completions(body: ChatRequest, _: None = Depends(_auth)) -> Any:
    if body.stream:
        raise HTTPException(400, "stream=false required in this build")
    llm = get_llm()
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    try:
        out = llm.create_chat_completion(
            messages=messages,
            temperature=body.temperature,
            top_p=body.top_p,
            max_tokens=body.max_tokens,
        )
    except Exception as e:
        raise HTTPException(500, f"inference failed: {e}") from e

    # Normalize to OpenAI shape (llama-cpp already close)
    if isinstance(out, dict) and "choices" in out:
        out.setdefault("id", f"chatcmpl-{uuid.uuid4().hex[:12]}")
        out.setdefault("object", "chat.completion")
        out["model"] = body.model or MODEL_ALIAS
        return JSONResponse(out)

    # Fallback if library returns unexpected
    text = str(out)
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.model or MODEL_ALIAS,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
