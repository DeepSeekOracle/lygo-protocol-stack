# BUILDR USB Phase 2 — **COMPLETE** (Windows portable)

Canonical overlay: `I:\E Drive\LYGO_BUILDR_USB\` · portable root: `E:\LYGO_BUILDER_KEY\`

**Gate:** `verify_bootstrap.py --edition GROK_BUILDR --phase2` → `all_ok: true`

## Build

```powershell
E:\LYGO_BUILDER_KEY\scripts\build_phase2_complete.ps1
E:\LYGO_BUILDER_KEY\launchers\LYGO_Verify_Phase2.bat
```

Incremental sync (no full repack): `scripts\sync_overlay_to_builder_key.ps1` on stick.

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