@echo off
cd /d "%~dp0"
echo Public LYGO gateway on 127.0.0.1:9642 (chat only). Use --lan --i-consent only behind HTTPS.
py -3 -u src\public_gateway.py --port 9642 --backend ollama --model qwen2.5:3b
pause
