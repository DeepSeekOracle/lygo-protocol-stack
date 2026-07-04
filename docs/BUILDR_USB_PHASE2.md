# BUILDR USB Phase 2 (complete on Windows)

Canonical sources: `I:\E Drive\LYGO_BUILDR_USB\phase2\` and `E:\LYGO_BUILDER_KEY\phase2\`.

## Build

```powershell
E:\LYGO_BUILDER_KEY\scripts\build_phase2_complete.ps1
```

## Artifacts

- `images/lygo_core.tar.gz` + SHA256 + HMAC sig  
- `mnt_core/` verified extract  
- `data/hermes_audit/audit_trail.log`  
- Supervisor http://127.0.0.1:9630  

## API

| Method | Path | Body |
|--------|------|------|
| GET | `/health` | — |
| GET | `/GetTrainingSignal` | — |
| POST | `/Supervise` | `{"agent_id","tool_call":{"name","args"}}` |
| POST | `/AnchorAudit` | — |

Linux squashfs/LUKS: see `phase2/LUKS_LINUX.md` on stick.

Δ9Φ963