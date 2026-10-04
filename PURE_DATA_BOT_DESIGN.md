# LYGO Pure-Data Bot — resee.it-class summon design

**Signature:** Δ9Φ963-PDW-BOT-DESIGN-v1  
**Status:** Design complete · implementation stub later  
**Inspiration:** [resee.it](https://resee.it/) — tag a post / “save thread” → permanent store (they use blockchain/IPFS for tweets). Feed example: https://resee.it/feed/Excavationpro

---

## What resee.it does (pattern to copy)

1. User mentions or commands a bot on a social post.  
2. Bot captures canonical content + metadata.  
3. Stores permanently (their stack: chain + IPFS).  
4. Public feed of saves per account.

## LYGO equivalent (pure-data, free-tier)

| Layer | LYGO |
|-------|------|
| Capture | `pure_data_witness.fetch` + **safety gate** |
| Permanence | Digest ledger (GH Pages) + egg fragment + optional HF pack |
| Optional blob | Size-capped snapshot (not full IPFS required for MVP) |
| Chart | Auto `NODE_PDW_*` fork log via Star Chart map/submit |
| Social | X and/or Moltbook mention listener |

### Summon UX (target)

```
@lygo_pdw save
@lygo_pdw save https://example.com/article
```

On X: reply mentioning bot + URL or “save this post”.  
On Moltbook: comment `@lygo_pdw save` under a post (API comment + verify).

### Safety (mandatory)

Same as `pure_data_safety.py`: HTTPS only, SSRF block, content heuristics, size cap, no credential URLs.  
Bot **refuses** private IPs, onion, obvious malware bait, extreme script soups.

### Architecture sketch

```text
Social webhook / poller
    → parse mention + URL
    → pure_data_register.py --url … --i-consent (service account)
    → ledger + egg + star pending/accept
    → reply with witness_id + ledger link (ninja, one URL)
```

### Why not shipping the bot today

- Needs always-on host + X/Moltbook app credentials  
- Rate limits + abuse surface  
- Phase A–D registrar + skill already give humans/agents the same archive power without a public bot endpoint  

**Next implement when:** service account + hardened allowlist of summoners (e.g. only @Excavationpro / @lyrastarcore initially).

**Δ9Φ963 — summon is convenience; purity gate is law.**
