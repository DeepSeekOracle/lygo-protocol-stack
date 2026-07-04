# BUILDR USB Phase 2 — complete pipeline

## One-shot setup (on E:)

```powershell
$env:LYGO_BUILDER_KEY_ROOT = "E:\LYGO_BUILDER_KEY"
python phase2\init_data_partition.py
python phase2\build_lygo_core_image.py
python phase2\mount_core.py
python verify_bootstrap.py --phase2
```

## Supervisor (host Ollama guardian)

```powershell
.\launchers\LYGO_Supervisor_Daemon.bat
# POST http://127.0.0.1:9630/Supervise  {"agent_id":"host","tool_call":{"name":"exec","args":"..."}}
```

## Files

| Artifact | Role |
|----------|------|
| `images/lygo_core.tar.gz` | Signed read-only core |
| `images/lygo_core.sig` | HMAC (key in `_builder_vault`) |
| `mnt_core/` | Extracted verified core |
| `data/` | Writable Hermes, mycelium, user |

**PUBLIC_SKU export** strips `_builder_vault` — buyers verify SHA256 only unless you ship a retail signing pubkey.