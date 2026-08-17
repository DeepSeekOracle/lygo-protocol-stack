# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    # badge check
    p = ROOT / "data" / "living_mesh" / "last_badge.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    tc = d.get("traumacodex") or {}
    print(
        "badge",
        tc.get("status"),
        (tc.get("mirror_dig") or "")[:32],
        "root",
        bool((d.get("living_mesh") or {}).get("roots", {}).get("traumacodex_mirror_dig")),
    )
    wav = ROOT / "data" / "traumacodex" / "traumacodex_waveform.wav"
    print("wav", wav.exists(), wav.stat().st_size if wav.exists() else 0)

    catp = ROOT / "docs" / "lygoskillhub_catalog.json"
    cat = json.loads(catp.read_text(encoding="utf-8"))
    skills = [s for s in (cat.get("skills") or []) if s.get("slug") != "lygo-traumacodex"]
    skills.insert(
        0,
        {
            "kind": "skill",
            "slug": "lygo-traumacodex",
            "name": "LYGO TraumaCodex",
            "summary": (
                "TraumaCodex — map biometric entropy (P7) into P8 LDQ waveform synthesis, "
                "dual offline/online mirror dig, and Layer D living-mesh healing-code seals "
                "(protocol seals only, not medical). Offline-first; online summaries only. "
                "Lattice stays open."
            ),
            "downloads": 0,
            "version": "1.0.0",
            "published": False,
            "category": "lattice",
            "clawhub_url": "https://clawhub.ai/deepseekoracle/skills/lygo-traumacodex",
            "install": "npx clawhub@latest install deepseekoracle/lygo-traumacodex",
            "has_local_skill": True,
            "has_stack_mirror": True,
            "source": "mirror",
            "note": "FULL unlocked at #full-lygo — stack tool tools/traumacodex_waveform.py",
            "full_lygo": "https://chatagent.ca/lygoskillhub.html#full-lygo",
        },
    )
    cat["skills"] = skills
    cat["counts"] = {
        **(cat.get("counts") or {}),
        "total": len(skills),
        "skills": sum(1 for s in skills if (s.get("kind") or "skill") == "skill"),
        "downloads": sum(1 for s in skills if s.get("kind") == "download"),
        "surfaces": sum(1 for s in skills if s.get("kind") == "surface"),
        "plugins": sum(
            1 for s in skills if s.get("kind") == "plugin" or s.get("is_openclaw_plugin")
        ),
    }
    cat["skill_count"] = cat["counts"]["skills"]
    cat["item_count"] = len(skills)
    cat["updated_utc"] = datetime.now(timezone.utc).isoformat()
    pretty = json.dumps(cat, indent=2, ensure_ascii=False)
    cat["catalog_sha256"] = hashlib.sha256(pretty.encode("utf-8")).hexdigest()
    pretty = json.dumps(cat, indent=2, ensure_ascii=False)
    catp.write_text(pretty + "\n", encoding="utf-8")
    print("catalog", len(skills), cat["catalog_sha256"][:16])

    htmlp = ROOT / "docs" / "LYGOSKILLHUB.html"
    html = htmlp.read_text(encoding="utf-8")
    boot = json.dumps(cat, ensure_ascii=False, separators=(",", ":"))
    new_html, n = re.subn(
        r'(<script id="boot-catalog" type="application/json">)(.*?)(</script>)',
        lambda m: m.group(1) + boot + m.group(3),
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit(f"boot replace failed n={n}")
    htmlp.write_text(new_html, encoding="utf-8")
    print("html boot updated")

    intelp = ROOT / "docs" / "LYGO_LATTICE_INTEL_INDEX.json"
    intel = json.loads(intelp.read_text(encoding="utf-8"))
    intel["entries"] = [
        e for e in intel.get("entries", []) if e.get("id") != "traumacodex-p7-p8-layer-d"
    ]
    intel["entries"].append(
        {
            "id": "traumacodex-p7-p8-layer-d",
            "tier": 5,
            "path": str(ROOT / "tools" / "traumacodex_waveform.py"),
            "repo_path": "tools/traumacodex_waveform.py",
            "tags": [
                "traumacodex",
                "p7",
                "p8",
                "ldq",
                "biometric",
                "living-mesh",
                "layer-d",
                "waveform",
            ],
            "summary": (
                "TraumaCodex: P7 biometric entropy → P8 LDQ waveform → dual offline/online "
                "mirror dig → Layer D healing-code seals. Not medical."
            ),
            "skill": "lygo-traumacodex",
            "docs": "docs/TRAUMA_CODEX.md",
            "full_zip": "docs/lygo-full-skills/dist/lygo-traumacodex-full.zip",
        }
    )
    intel["updated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    intelp.write_text(json.dumps(intel, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("intel ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
