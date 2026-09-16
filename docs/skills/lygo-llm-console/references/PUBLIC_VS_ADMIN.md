# Public kit vs admin

| | Public kit (this skill) | Admin / steward |
|--|--|--|
| Map scripts | No network | n/a |
| Runtime | After SHA-256 verify | Same source tree plus local engine/data |
| Write roots | kit `workspace/` + `save/` | May include steward disks (never in the zip) |
| Shell | `cmd.exe /c` without `\| & > < \` $`; P0 wipe block | Same in this version |
| Vaults | Not shipped | Steward media only |
| Bind | 127.0.0.1:9641 | `--lan --i-consent` for 0.0.0.0 |
| Engine | Operator-supplied b10988 CPU zip | Same |
