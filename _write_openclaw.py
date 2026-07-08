from pathlib import Path
ROOT = Path(r"I:\E Drive\lygo-protocol-stack")

def w(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    print("w", rel)

w("docs/BIOPHASE7_LYGO_OPENCLAW.md", """# Biophase7 -> LYGO-OpenClaw

**Source:** `2026Biophase7/LYGO-OpenClaw Full Build Bluep.txt`
**Stack path:** `lygo_openclaw/`
**CLI:** `python tools/lygo_openclaw.py`
**Install:** `python tools/install_lygo_openclaw.py`
**ClawHub:** `deepseekoracle/lygo-openclaw`
**Hybrid limb:** `lyra-openclaw` (browser, Discord, Moltbook, Clawnch)

## Philosophy

| Layer | Implementation |
|-------|----------------|
| P0 | `gatekeeper.py` -> stack `byte_entropy_filter` (32 KiB cap) |
| P1 | `memory.py` -> 12 fragments, `data/openclaw/mycelium` |
| P3 | `consensus.py` -> 3-6-9 harmonic (optional `multi_agent`) |
| P5 | `harmony.py` -> Light Code per action |
| Anchor | `anchor.py` -> `action_runs.jsonl` (honest ledger) |
| Limbs | `help`, `status`, `lattice`, `army-sentinel`, `flow-kit-path`, `hybrid-skill` |

## Kernel egg

| Item | Path |
|------|------|
| `egg_id` | `lygo-openclaw-v10` |
| Registry | `docs/OpenClawRegistry.json` |
| Plant | `python tools/openclaw_planter.py --i-consent` |

## Verify

```bash
python clawhub/mirrors/lygo-openclaw/scripts/self_check.py
python tools/lygo_openclaw.py run help
python -m pytest tests/test_lygo_openclaw.py -q
```
""")

w("docs/OpenClawRegistry.json", '{"signature":"D9F963-OPENCLAW-EGG-v1","updated_utc":0,"git_head":"pending","egg_count":1,"registry_merkle_root":"pending","eggs":[{"egg_id":"lygo-openclaw-v10","merkle_root":"pending","manifest_path":"data/openclaw/openclaw_egg_manifest.json"}],"ledger":"data/openclaw/action_runs.jsonl"}')

# openclaw_planter already planned - write full file
planter = (ROOT / "tools" / "openclaw_planter.py")
planter.write_text((ROOT / "tools" / "workflow_orchestrator_planter.py").read_text(encoding="utf-8").replace("lygo-sandcastle-v10", "lygo-openclaw-v10").replace("WorkflowOrchestratorRegistry.json", "OpenClawRegistry.json").replace("workflow_egg_manifest.json", "openclaw_egg_manifest.json").replace("SANDCASTLE", "OPENCLAW").replace("sandcastle", "openclaw").replace("lygo_sandcastle_kernel_egg", "lygo_openclaw_kernel_egg").replace("lygo_sandcastle.py", "lygo_openclaw.py").replace("BIOPHASE7_LYGO_SANDCASTLE.md", "BIOPHASE7_LYGO_OPENCLAW.md").replace("lygo_sandcastle/", "lygo_openclaw/").replace("example_sovereign.yaml", "framework.py").replace("orchestrator.py", "limbs.py").replace("workflow_orchestrator_planter", "openclaw_planter").replace("lygo-sandcastle", "lygo-openclaw"), encoding="utf-8")
# fix artifacts block manually
text = planter.read_text(encoding="utf-8")
old = '''    artifacts = [
        ("openclaw_cli", ROOT / "tools" / "lygo_openclaw.py"),
        ("openclaw_spec", ROOT / "docs" / "BIOPHASE7_LYGO_OPENCLAW.md"),
        ("package_readme", ROOT / "lygo_openclaw" / "README.md"),
        ("example_workflow", ROOT / "lygo_openclaw" / "workflows" / "framework.py"),
        ("orchestrator_core", ROOT / "lygo_openclaw" / "limbs.py"),
    ]'''
new = '''    artifacts = [
        ("openclaw_cli", ROOT / "tools" / "lygo_openclaw.py"),
        ("openclaw_spec", ROOT / "docs" / "BIOPHASE7_LYGO_OPENCLAW.md"),
        ("package_readme", ROOT / "lygo_openclaw" / "README.md"),
        ("framework", ROOT / "lygo_openclaw" / "framework.py"),
        ("limbs", ROOT / "lygo_openclaw" / "limbs.py"),
        ("gatekeeper", ROOT / "lygo_openclaw" / "gatekeeper.py"),
    ]'''
if "example_workflow" in text:
    text = text.replace(old.replace("framework.py", "framework.py"), new)
# simpler replace
import re
text = re.sub(r'artifacts = \[.*?\]', new, text, count=1, flags=re.S)
text = text.replace('python tools/lygo_openclaw.py run lygo_openclaw/workflows/framework.py', 'python tools/lygo_openclaw.py run help')
text = text.replace('workflow_egg_manifest', 'openclaw_egg_manifest')
planter.write_text(text, encoding="utf-8")
print("w tools/openclaw_planter.py")
