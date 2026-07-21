# Hugging Face Docker Space — OpenAI-compatible LYGO Qwen uncensored API
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/data/huggingface \
    MODEL_DIR=/data/models \
    PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Prefer CUDA wheel when Space has GPU; fall back to CPU wheel for build
RUN pip install --upgrade pip && \
    (pip install llama-cpp-python==0.3.8 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 \
     || pip install llama-cpp-python==0.3.8) && \
    pip install -r requirements.txt

COPY app /app/app
RUN mkdir -p /data/huggingface /data/models

EXPOSE 7860
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
