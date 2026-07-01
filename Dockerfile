# LYGO Protocol Stack — community node (Python + optional C/Rust build tools)
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="LYGO Protocol Stack Node"
LABEL org.opencontainers.image.source="https://github.com/DeepSeekOracle/lygo-protocol-stack"
LABEL lygo.signature="Δ9Φ963-PHASE2-DEPLOYMENT"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-docker.txt* ./
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ -f requirements-docker.txt ]; then pip install --no-cache-dir -r requirements-docker.txt; fi

COPY . .

ENV LYGO_STACK_ROOT=/app
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=60s --timeout=120s --start-period=30s --retries=3 \
  CMD python tools/verify_alignment_badge.py --quick --format=json || exit 1

EXPOSE 8787

CMD ["python", "tools/node_api_server.py", "--host", "0.0.0.0", "--port", "8787"]