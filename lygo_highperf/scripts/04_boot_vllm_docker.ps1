# LYGO High-Perf — optional vLLM Docker path (experimental GGUF)
# Requires: Docker Desktop running + NVIDIA Container Toolkit
# Note: On 8GB VRAM, prefer 03_boot_llamacpp.ps1 — vLLM GGUF is experimental & VRAM-heavy.
param(
  [string]$Root = "D:\LYGO_HIGHPERF",
  [string]$Tokenizer = "Qwen/Qwen3.6-35B-A3B",
  [int]$Port = 8001,
  [int]$MaxLen = 4096
)
$ErrorActionPreference = "Stop"
$models = Join-Path $Root "models"
$gguf = Join-Path $models "LYGO-Qwen3.6-35B-A3B-Uncensored-Q4_K_M.gguf"
if (-not (Test-Path $gguf)) { & (Join-Path $Root "scripts\01_stage_models.ps1") }

docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Start Docker Desktop first." }

# Compose file
$compose = Join-Path $Root "docker-compose.vllm.yml"
@"
services:
  lygo-vllm:
    image: vllm/vllm-openai:latest
    container_name: lygo-vllm-uncensored
    runtime: nvidia
    ipc: host
    ports:
      - "${Port}:8000"
    volumes:
      - ${models}:/app/model:ro
    environment:
      - HUGGING_FACE_HUB_TOKEN=`${HF_TOKEN:-}
      - NVIDIA_VISIBLE_DEVICES=all
    command:
      - --model
      - /app/model/LYGO-Qwen3.6-35B-A3B-Uncensored-Q4_K_M.gguf
      - --tokenizer
      - $Tokenizer
      - --max-model-len
      - "$MaxLen"
      - --dtype
      - auto
      - --gpu-memory-utilization
      - "0.90"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
"@ | Set-Content $compose -Encoding utf8

Write-Host "Starting LYGO vLLM (experimental) on :$Port ..."
Write-Host "If OOM: use scripts\03_boot_llamacpp.ps1 instead."
docker compose -f $compose up -d
docker logs -f lygo-vllm-uncensored
