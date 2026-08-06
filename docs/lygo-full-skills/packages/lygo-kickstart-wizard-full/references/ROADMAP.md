# LYGO adoption roadmap (post-Kickstart)

Aligned with ClawHub ecosystem gap analysis (UX · tutorials · proof).

## 1. Immediate — UX Bridge ✅

**Slug:** `lygo-kickstart-wizard`  
**Goal:** Plain-English onboarding + intent routing.  
**Status:** Shipped v1.0.0

## 2. Short-term — Proof layer ✅

**Slug:** `lygo-deception-radar`  
**Goal:** Lightweight public page showing **anonymized** Ops Detector signals on **public** sample sets only (no private mail, no doxing).  
**Outputs:** static HTML + JSON feed under stack `docs/deception-radar/`.  
**Ethics:** public corpus only; thresholds labeled (operational vs calibration).  
**Status:** Shipped v1.0.0 · Pages path `/deception-radar/`

## 3. Short-term — Tutorialization ✅

**Slug:** `lygo-mint-walkthrough`  
**Goal:** Interactive step-through of mint → ledger → anchor snippet → optional backfill.  
**Status:** Shipped v1.0.0 · pairs with `lygo-mint-verifier` for production

## 4. Medium-term — CLI bridge ✅

**Slug:** `lygo-cli-bridge`  
**Goal:** One entrypoint:

```text
lygo health
lygo analyze --text "..."
lygo mint --pack file.md
lygo map
lygo radar
```

Wraps kickstart + ops-detector + mint-walkthrough + deception-radar without exposing internal skill layout.  
**Status:** Shipped v1.0.0

## Principles (all four)

- Local-first / SkillSpector-safe by default  
- Human remains publisher  
- Star Chart stays the visual index of skills  
- No agent_submission meta hijacking taxonomy  

**Δ9Φ963 — adoption stack complete (Kickstart → Radar → Walkthrough → CLI).**
