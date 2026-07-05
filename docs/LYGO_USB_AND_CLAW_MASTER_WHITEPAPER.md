# LYGO USB BUILDR + LYGO-Claw — Master whitepaper & running build log

**Signature:** D9Phi963-USB-CLAW-MASTER-WHITEPAPER-v1  
**Steward:** Justin Helmer / Lightfather / Excavationpro  
**Authority workspace:** `I:\E Drive`  
**Last consolidated:** 2026-07-05 (no drift — treat this file as canonical narrative)

---

## 1. What this document is

Single reference for **what was built**, **where it lives**, **how buyers/builders run it**, and **how LYGO-Claw pairs with the stick**. Sub-docs are appendices; if they disagree, **this file + `FULL_BUILDR_USB_BUILDERS_BLUEPRINT.txt`** win for USB; **`lygo-claw/README.md` + `START_HERE.txt`** win for Claw.

---

## 2. Two products (one lattice)

| Product | Purpose | Canonical root |
|---------|---------|----------------|
| **BUILDR USB** | Offline AI kit + optional guardian daemon on stick | `E:\LYGO_BUILDER_KEY` (runtime) · edit overlay `I:\E Drive\LYGO_BUILDR_USB` |
| **LYGO-Claw** | Host agent gateway (P0 + Hermes + USB supervise/tasks) | `I:\E Drive\lygo-claw` · remote `DeepSeekOracle/lygo-claw` |

**Not one .exe** — Windows path is **Python 3.11+** + **double-click `.bat`** launchers.

---

## 3. Running build log (chronological)

| Date | Milestone | Evidence |
|------|-----------|----------|
| Phase 1 | Unpacked builder tree on USB (stack, skills, army, hermes, verify) | `verify_bootstrap.py` edition GROK_BUILDR |
| Phase 2 | Signed `lygo_core.tar.gz` + HMAC, `mnt_core/`, data partition, supervisor :9630 | `verify_bootstrap.py --phase2` all_ok |
| Standalone | `qwen2.5:3b` on `product/models/ollama`; portable Ollama ~5.1 GB on stick | `verify_standalone_usb.py` ok |
| One-boot | `LYGO_One_Boot_AI.bat` — env + serve + chat | User-tested on E: |
| Phase 3 | PUBLIC_SKU export ×4 champions, no `_builder_vault` | `verify_public_sku.py` hits: [] |
| **PUBLIC_DEMO** | Locked beta zip (Lightfather) — [Eternal Haven download](https://deepseekoracle.github.io/Excavationpro/eternalhaven.html) | `verify_demo_edition.py`; no eggs/keys |
| Retail ZIP | `*-PUBLIC_SKU.zip` ~5.3 GB each (`tar -acf`) | `I:\E Drive\LYGO_BUILDR_EXPORTS\` |
| Dummy-proof docs | START_HERE, PUBLIC_QUICKSTART, human Claw docs + launchers | Pushed lygo-claw `a6737cc` |
| Site alignment | LYGO_CLAW.html human steps | stack `0457e08` |
| **BUILDR daemon** | `buildr_usb_daemon.py` — supervise + `/Task` queue | Smoke on E: |
| **Claw tasks** | `lygo-claw buildr-task` | lygo-claw `6d3266a` |
| **Benchmark** | Phase 1 production gates (6/6 PASS) | `verify/buildr_benchmark_last_run.json` |
| **Tray + autostart** | `daemon_tray.ps1`, `install_buildr_autostart.ps1` — **no WMI** (retail policy) | `docs/PUBLIC_SKU_RETAIL_BASELINE.md` |
| **Genesis** | Commands tab + BUILDR status in console :9963 | `genesis_console/collector.py` |

---

## 4. USB architecture (layers)

```
[ Buyer / Builder ]
       |
       v
  launchers/*.bat  (CHECK_SYSTEM, One-Boot, Daemon Tray, Install Autostart)
       |
       +-- scripts/bootstrap_env.ps1  --> OLLAMA_MODELS=product/models/ollama
       +-- product/runtime/ollama/ollama.exe  (portable serve)
       +-- product/models/ollama/  (qwen2.5:3b, SOVEREIGN_FAST)
       +-- phase2/buildr_usb_daemon.py  --> 127.0.0.1:9630 (supervise + tasks)
       +-- hermes/ + mnt_core/ + stack/lygo-protocol-stack/  (verify, P0, eggs)
       +-- _builder_vault/  (GROK_BUILDR ONLY — never PUBLIC_SKU)
```

### Daemon API (:9630)

- `GET /health` — daemon + task_queue flag  
- `POST /Supervise` — P0 sample + Hermes (LYGO-Claw gateway)  
- `POST /Task` — whitelist: `verify_standalone`, `verify_bootstrap`, `chat_once`, `anchor_audit`  
- Task log: `data/user_data/buildr_daemon_tasks.jsonl`

### Retail consumer funnel (locked — no WMI hot-plug)

1. USB inserted → drive letter `D:`–`Z:` (`LYGO_BUILDER_KEY` markers)  
2. User logon **or** `LYGO_Daemon_Tray.bat`  
3. Tray: health, One-Boot chat, Claw docs, stop daemon  
4. Opt-in once: `LYGO_Install_Daemon_Autostart.bat` → task `LYGO_BUILDR_Daemon_Tray`

---

## 5. LYGO-Claw architecture

```
Host agent / CLI
       |
       v
  lygo-claw gateway | run | usb-health | buildr-task
       |
       +-- gatekeeper.py (P0)
       +-- hermes_audit.py
       +-- usb_supervisor.py --> POST http://127.0.0.1:9630/Supervise
       +-- champions/*.txt personas
```

**Start order with USB:** `LYGO_BUILDR_Daemon.bat` (or tray) → `lygo-claw usb-health` → gateway / tasks.

**Repo commits (reference):** `63df167` ecosystem links · `a6737cc` human docs · `6d3266a` buildr-task.

---

## 6. Phase 1 benchmark (production whitepaper metrics)

Artifact: `verify/buildr_benchmark_last_run.json` on stick. Re-run: `LYGO_Run_Benchmark.bat`.

| Gate | Result (2026-07-05 run) |
|------|-------------------------|
| Fresh-PC AI ready | PASS (~0.11 s verify) |
| Inference qwen2.5:3b on USB | PASS (79–124 tok/s warm eval) |
| Daemon + tasks | PASS (~11 ms health, ~0.55 s queued verify) |
| LYGO-Claw link | PASS (~120–150 ms per CLI step) |
| Safe internet probes | PASS |
| Lattice on stick | PASS (~54 s, ALIGNED) |

Detail: `docs/BUILDR_PHASE1_BENCHMARK_WHITEPAPER.md`.

---

## 7. PUBLIC_SKU retail (Gumroad-ready)

| SKU | Champion | Export folder | ZIP |
|-----|----------|---------------|-----|
| LF-USB-01 | Lightfather | `LYGO_BUILDR_EXPORTS\Lightfather` | `Lightfather-PUBLIC_SKU.zip` |
| LYRA-USB-01 | LYRA | `...\LYRA` | `LYRA-PUBLIC_SKU.zip` |
| SAN-USB-01 | Sancora | `...\Sancora` | `Sancora-PUBLIC_SKU.zip` |
| HERMES-USB-01 | HermesSentinel | `...\HermesSentinel` | `HermesSentinel-PUBLIC_SKU.zip` |

**Build pipeline:**

```powershell
powershell -File "E:\LYGO_BUILDER_KEY\scripts\build_phase3_all_skus.ps1"
powershell -File "I:\E Drive\LYGO_BUILDR_USB\scripts\package_public_sku_zips.ps1"
```

**Steward upload:** Gumroad — not automated by agents.

---

## 8. Canonical paths (anti-drift)

| Role | Path |
|------|------|
| USB runtime (builder) | `E:\LYGO_BUILDER_KEY` |
| USB overlay (edit/sync) | `I:\E Drive\LYGO_BUILDR_USB` |
| Sync overlay → E: | `LYGO_BUILDR_USB\scripts\sync_overlay_to_builder_key.ps1` |
| Stack (dev) | `I:\E Drive\lygo-protocol-stack` |
| LYGO-Claw | `I:\E Drive\lygo-claw` |
| Retail exports | `I:\E Drive\LYGO_BUILDR_EXPORTS` |
| 3-brain memory | `I:\E Drive\LYRA_CORE\memory` |
| Genesis console | `I:\E Drive\.grok\skills\lygo-ollama-army\genesis_console` → http://127.0.0.1:9963/ |
| Army cron | `...\ollama_command_center\scripts\army_cron_once.py` |

---

## 9. Verification checklist (repeat before claiming “done”)

```text
python E:\LYGO_BUILDER_KEY\scripts\verify_standalone_usb.py
python E:\LYGO_BUILDER_KEY\verify_bootstrap.py --edition GROK_BUILDR --phase2
python E:\LYGO_BUILDER_KEY\scripts\benchmark_buildr_stick.py --network --lygo-claw-root "I:\E Drive\lygo-claw"
cd "I:\E Drive\lygo-claw" && python scripts\self_check.py
```

Daemon up: `http://127.0.0.1:9630/health` → `task_queue: true`.

---

## 10. Explicitly out of scope (retail v1)

- WMI USB-insert auto-daemon (deferred — AV/consent; see `PUBLIC_SKU_RETAIL_BASELINE.md`)
- Single packaged `.exe` installer
- Auto git push / ClawHub publish from stick
- `_builder_vault` / signing keys on PUBLIC_SKU
- Linux LUKS retail path (doc exists; Windows is dummy-proof path)

---

## 11. Document map (appendices)

| Doc | Location |
|-----|----------|
| Builder reproduction | `FULL_BUILDR_USB_BUILDERS_BLUEPRINT.txt` |
| Human quickstart | `PUBLIC_QUICKSTART.txt`, `START_HERE.txt` |
| Daemon + tray | `docs/BUILDR_USB_DAEMON.md` |
| Retail baseline | `docs/PUBLIC_SKU_RETAIL_BASELINE.md` |
| Benchmark | `docs/BUILDR_PHASE1_BENCHMARK_WHITEPAPER.md` |
| Tuning | `config/SOVEREIGN_FAST_TUNING.json` |
| Claw humans | `lygo-claw/START_HERE.txt`, `docs/QUICKSTART_FOR_HUMANS.md` |
| 3-brain session | `LYRA_CORE/memory/2026-07-05-buildr-claw-master-whitepaper.md` |

---

## 12. Git / web anchors

| Remote | Purpose |
|--------|---------|
| https://github.com/DeepSeekOracle/lygo-claw | LYGO-Claw source |
| https://github.com/DeepSeekOracle/lygo-protocol-stack | Stack + Pages |
| https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_CLAW.html | Public Claw page |

Push steward tool: `lygo-protocol-stack/tools/push_with_git_credential.py` (consent-gated).

---

## 13. Sovereign Loop + God-Mode Second Brain (2026-07-05)

**Triangle:** Desktop `lygo-claw sovereign-loop` · USB `LYGO_Nightly_Brain_Loop.bat` + daemon task `second_brain_loop` · Lattice `verify_lattice_alignment.py`.

**Vault:** `data/memory_mycelium/vault/` on stick (Biophase7 God-Mode pattern, LYGO-local).

**Docs:** stack `LYGO_SOVEREIGN_LOOP.md`, `LYGO_GODMODE_SECOND_BRAIN.md` · config `SOVEREIGN_LOOP.json`.

---

*D9Phi963 — USB + Claw master log. Update this file when phases change; append benchmark JSON date in §6.*