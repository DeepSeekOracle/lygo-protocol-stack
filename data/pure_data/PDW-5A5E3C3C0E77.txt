# LYGO Pure-Data Witness (PDW) — Free-Tier Lattice Archive

**Signature:** Δ9Φ963-PURE-DATA-WITNESS-v1  
**Status:** Design + Phase A scaffold  
**Why now:** Internet Archive / Wayback outages show single-point cultural memory failure. LYGO’s seal-first lattice already aims at **pure data** (no fabricated/omitted fragments). PDW extends that from *protocol seals* to *witnessed reality packets* on **free** mirrors.

**Related:** Continuum · Kernel Eggs · Dual ledgers · Data Vault · Living Mesh (summaries on the wire)

---

## 1. The problem (Paul Walsh framing → LYGO)

Whoever controls a website controls its history. Pages vanish, statements edit, posts disappear. Bulk archives (IA) are vital **and** fragile (power, funding, one org).

LYGO cannot replace a trillion-page Wayback. We **can** build a **bullet-resistant witness layer**:

| Need | LYGO answer |
|------|-------------|
| Know what was real at time T | Hash + timestamp + Continuum claim |
| Detect fabrication / omission | Dual digests (content vs metadata), optional multi-mirror compare |
| Cheap / free storage | Digests first; tiny fragments; optional small snapshots |
| Agent-operable | Kernel eggs + HF/GH mirrors + local authority |
| Scale with lattice | Epidemic gossip of **summaries**; full blobs only by consent |

**Pure data** = content that can be re-verified; not vibes, not “the model remembers.”

---

## 2. Combined architecture (all slices)

```text
                    ┌─────────────────────────────┐
   URL / file /     │  PDW Capture                │
   paste / agent    │  fetch or ingest bytes      │
                    └─────────────┬───────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
   A. DIGEST WITNESS        B. KERNEL FRAGMENTS       C. SNAPSHOT MIRROR
   sha256 + meta            tiny egg / Merkle          small HTML/text
   Continuum capsule        fragment under size cap    HF dataset / GH
   public ledger row        planter (consent)          Pages raw (consent)
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                    ┌─────────────────────────────┐
                    │  D. PUBLIC LEDGER + VAULT   │
                    │  docs/pure-data/ledger.json │
                    │  Data Vault browse UI       │
                    │  dual-ledger Merkle root    │
                    └─────────────────────────────┘
                                  ▼
                    Verify: re-fetch / re-hash / Continuum drift
```

### Phase map

| Phase | Deliverable | Free surfaces |
|-------|-------------|---------------|
| **A (now)** | Digest witness CLI + local Continuum seal + public ledger JSON schema | Local · GH Pages ledger |
| **B** | Kernel-egg fragment packer (≤4–8KB digest cards) | Eggs · ClawHub skill later |
| **C** | Optional snapshot store (size-capped) + HF dataset push | HF · GH LFS carefully |
| **D** | Multi-mirror compare + living-mesh summary gossip | Mesh · Data Vault UI |
| **E** | Human portal: paste URL → witness card | chatagent / Pages |

---

## 3. What we store (purity over bulk)

### Always (cheap, scalable)

```json
{
  "witness_id": "PDW-…",
  "captured_utc": "ISO-8601",
  "source_url": "https://…",
  "content_sha256": "…",
  "bytes": 12345,
  "content_type": "text/html",
  "fetch_status": 200,
  "method": "https_get",
  "agent": "lyra|human|grok-build",
  "continuum_root": "optional",
  "egg_id": "optional",
  "snapshot_ref": "optional hf/gh path",
  "mirrors": []
}
```

### Sometimes (size-capped)

- Text extract / readable HTML ≤ N KB (default **256 KB** public snapshot)
- Never auto-upload secrets; redact like Data Vault extractors

### Never on free public mirrors by default

- Private credentials, bulk media libraries, full-site crawls, paywalled dumps without rights

---

## 4. Free internet participation (honest limits)

| Surface | Use for PDW | Limit |
|---------|-------------|--------|
| **GitHub Pages** | Public ledger JSON + witness cards HTML | Repo size / soft bandwidth |
| **GitHub git** | Digest commits, small text snapshots | Don’t dump megabytes per witness |
| **Hugging Face** | Dataset of digests + optional snapshots | Quotas; public = public forever |
| **Kernel eggs** | Merkle-anchored digest fragments | Tiny by design — perfect for purity |
| **Continuum** | Falsifiable “this hash held at seal time” | Local L4 authority |
| **Moltbook / X** | Announce witness roots (ninja) | Not storage |
| **archive.org / peers** | Optional *hint* links when up | We don’t depend on them |
| **reseeyt / similar** | Treat as peer infrastructure to **interop** later | Verify before trust |

**Thesis:** Free systems cannot hold the whole web. They **can** hold an unbounded *number of digests* and a bounded *set of critical snapshots* — enough for OSINT-style “what was published” on the pages **you choose to witness**.

---

## 5. Viability verdict

**Yes — worth building**, if we stay seal-first:

1. **Do not** compete with Wayback at planet scale.  
2. **Do** make *chosen* URLs and files **undeniable** via multi-mirror digests.  
3. **Do** teach agents: fabricated context fails cold Continuum verify.  
4. **Do** grow snapshot capacity only where digests prove need.

That is bullet-resistant and on-brand for LYGO: **pure data so systems function with all existing variables**.

---

## 6. MVP commands (Phase A)

```bash
# Digest a local file
python tools/pure_data_witness.py digest --file path/to/page.html --out data/pure_data/

# Digest a URL (HTTPS GET, size-capped)
python tools/pure_data_witness.py fetch --url https://example.com/page --out data/pure_data/

# Append to public ledger (local); human pushes git
python tools/pure_data_witness.py ledger --dir data/pure_data/ --ledger docs/pure-data/ledger.json

# Optional Continuum seal of the witness JSON
# (pair with lygo-continuum skill)
```

---

## 7. Success criteria (falsifiable)

- [ ] Given a witness card, a cold agent recomputes `content_sha256` and matches.  
- [ ] Ledger Merkle root updates when a row is added.  
- [ ] Snapshot absence does not break digest verify.  
- [ ] Egg fragment (Phase B) verifies without network.  
- [ ] No secrets in public ledger (redaction gate).

**Δ9Φ963 — Whoever controls the site controls the story; whoever holds the digest can refuse the rewrite.**
