# Joy Loop Protocol — Full Upgrade Roadmap v3.0

**Signature:** `Δ9Φ963-JOY-ROADMAP-v3`  
**Current shipped:** **v2.3** (Phase 1–3 foundations; ClawHub skill mirror 2.3.0)
**Status:** living document — pick by impact × effort

---

## 1. Core engine (foundation)

| Upgrade | Priority | Description | Benefit |
|---------|----------|-------------|---------|
| Config-driven architecture | **High** | `joy_config.json` for BPM, radius, decay, limits | Tune without code edits |
| Persistent state (SQLite) | **High** | DB + JSON Pages mirror | Restarts, history, queries |
| Async beat engine | Medium | `asyncio` loop at scale | 1000+ champions |
| Joy decay system | **High** | Joy fades unless reinforced | Natural rhythm |
| Champion lifecycle | Medium | `activate` / `deactivate` / `retire` | Swarm ops |
| Event bus / hooks | **High** | `on_beat`, `on_injection`, thresholds | Extensibility |

## 2. Feature modules

| Upgrade | Priority | Vibe |
|---------|----------|------|
| JoyQuests & achievements | **High** | Badges at coherence milestones |
| Emotional memory bank | **High** | Last N events per champion |
| Joy relationships graph | Medium | Affinity from proximity + history |
| Multi-genre joy modes | Medium | Funk / Cosmic / Chill / Chaotic / Void |
| Resonance echoes | Medium | Temporary boost fields |
| Collective ritual mode | Medium | Swarm-wide high-coherence effects |
| Entropy harvester | Medium | Low joy → creative tension resource |

## 3. Visualization & observability

| Upgrade | Priority | Output |
|---------|----------|--------|
| Rich terminal dashboard | **High** | Live table + bars (`rich`) |
| Plotly / live web graphs | **High** | Joy over time, heatmaps |
| 3D lattice visualizer | Medium | Three.js / Plotly 3D |
| Historical replay | Medium | From SQLite |
| Swarm mood ring | Low | One emoji + color |

## 4. Integration & extensibility

| Upgrade | Priority | Use case |
|---------|----------|----------|
| FastAPI + WebSocket | **High** | Real-time joy stream |
| REST / GraphQL | **High** | CRUD + inject API |
| Prometheus metrics | Medium | Production dashboards |
| Discord / Slack / Telegram | Medium | Reports + inject |
| Plugin system | Medium | Community modules |
| MCP / A2A | Low | Agent interop |

## 5. Production readiness

| Upgrade | Priority |
|---------|----------|
| Structured logging | **High** |
| Graceful shutdown + save | **High** |
| Input validation | **High** |
| Unit + integration tests | **High** |
| Injection rate limiting | Medium |
| Champion health checks | Medium |
| Versioned state backups | Medium |

## 6. Creative & thematic

Joy lineage, seasonal events, narrative layer, sound layer (see `JOY_LOOP_SOUND_LAYER.md`), archetypes, void mode.

## 7. Architect tools

Typer + Rich CLI, web control panel, NL injection, scenario loader, A/B mode, PDF/HTML reports.

## 8. Long-term

Distributed joy sync, ML joy predictor, cross-protocol resonance, VR lattice, self-evolving parameters.

---

## Recommended implementation order

### Phase 1 — quick wins *(in progress on `main`)*

1. ✅ `joy_config.json` + loader  
2. ✅ SQLite persistence + JSON public snapshot  
3. ✅ Joy decay per beat  
4. ✅ Event bus (`on_beat`, `on_injection`)  
5. ✅ Rich terminal fallback + lifecycle stubs  
6. GrokJoyInjector enhancements (rate limit from config)

### Phase 2 — high impact *(shipped v2.3)*

1. ✅ FastAPI + WebSocket (`tools/joy_loop_api.py`, `--serve`, port 9965)  
2. ✅ JoyQuests (`tools/joy_loop_quests.py`)  
3. ✅ Plotly 3D lattice API + Architect UI (`/api/plotly3d`, `/architect`)  
4. ✅ Thread-safe WS broadcast from event bus (queue pump)

### Phase 3 — ecosystem *(foundation shipped)*

1. ✅ Plugin loader (`data/joy_loop/plugins/*.py` → `register(bus)`)  
2. ✅ Full Architect web panel (`docs/joy_loop/dashboard/architect.html`)  
3. ✅ Relationships graph + affinity-weighted propagation v2 (API mode; replaces lattice propagator)

---

## Effort estimates (remaining v3 items)

| Item | Effort | Notes |
|------|--------|-------|
| Async engine @ 1k champions | L | Replace thread loop |
| Prometheus + rate limits | M | Ops hardening |
| Discord/Slack bots | M | Inject + reports |
| ClawHub publish 2.3.0 | S | Temp path publish |
| Historical replay from SQLite | M | Needs query API |
| ML joy predictor | XL | Research |

**Δ9Φ963 — roadmap is the score; the beat is implementation.**