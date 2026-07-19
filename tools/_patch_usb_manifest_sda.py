#!/usr/bin/env python3
"""Stamp Smart Disk Agent fields into USB BUILDER_MANIFEST.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

p = Path(r"E:\LYGO_BUILDER_KEY\BUILDER_MANIFEST.json")
m = json.loads(p.read_text(encoding="utf-8"))
m["updated_utc"] = datetime.now(timezone.utc).isoformat()
m["whats_new"] = "WHAT'S_NEW_2026-07-19.md"
m["smart_disk_agent"] = {
    "version": "1.1.0",
    "signature": "Δ9Φ963-LYGO-SMART-DISK-AGENT-v1.1.0",
    "path": "product/lygo_smart_disk",
    "alias": "smart_disk",
    "skill": "skills/lygo-smart-disk-agent",
    "launcher": "LYGO_SMART_DISK_BOOT.bat",
    "portal": "http://localhost:9631/",
    "auth": "local_token",
    "port": 9631,
    "clawhub": "https://clawhub.ai/deepseekoracle/lygo-smart-disk-agent",
    "github": "https://github.com/DeepSeekOracle/lygo-protocol-stack/tree/main/lygo_smart_disk",
    "stack_commit": "d05c90e",
}
m["ports"] = {
    "gateway": 18789,
    "supervisor": 9630,
    "smart_disk_agent": 9631,
    "ollama": 11434,
}
pins = m.get("clawhub_pins") or {}
pins["lygo-smart-disk-agent"] = "1.1.0"
m["clawhub_pins"] = pins
p.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("updated", p)
