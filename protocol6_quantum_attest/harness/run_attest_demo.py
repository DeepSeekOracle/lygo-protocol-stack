#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "python"))
from hardware_attest import attestation_seal, validate_against  # noqa: E402

if __name__ == "__main__":
    seal = attestation_seal(extra="LYGO-P6-DEMO")
    ok = validate_against(seal["seal"], extra="LYGO-P6-DEMO")
    print(json.dumps({**seal, "self_validate": ok}, indent=2))
    raise SystemExit(0 if ok else 1)