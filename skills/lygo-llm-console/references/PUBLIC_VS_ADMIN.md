# Public kit vs admin console

| | **Public (this skill + zip)** | **Admin / steward** |
|--|--|--|
| Path | `lygo-llm-console-public.zip` · ClawHub tentacle | `lygo-protocol-stack/lygo_llm_console/` and any `F:\LYGO` copy |
| ClawHub | Yes — map only | **No** |
| Write roots | `workspace` + `save` inside the kit | May include steward disks (never in the zip) |
| `run_cmd` | Absent | Absent in v1 even on admin |
| Vaults / keys | Not shipped | Stay on steward media |
| Default bind | `127.0.0.1:9641` | Same unless `--lan --i-consent` |
| Engine | Operator places ggml-org `llama-server.exe` | Same, plus optional local cache |
| CANON | Dual ledgers / Star Chart remain CANON | Same |

If a tree contains steward vault paths, Gitea passwords, or `LYGO_SERVER_KEYS`, it is **admin**. Do not publish it.
