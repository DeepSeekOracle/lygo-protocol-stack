# Changelog — LYGO Protocol Stack

## [Biophase7 PC lattice hardening] — 2026-07-04

**Signature:** `Δ9Φ963-BIOPHASE7-HARDENING-v1`

### Added
- `docs/LIGHTFATHER_FINAL_ARCHITECT_ADDENDUM.md`, `P0_HONEST_SPEC.md`, `CRYPTO_LATTICE_SEPARATION.md`
- `protocol0_nano_kernel/src/python/byte_entropy_filter.py` (honest name + zlib diagnostics)
- `tools/calibrate_byte_entropy_filter.py`, `tools/run_parity_tests.py`, `tools/run_pc_lattice_hardening_audit.py` v1.1
- `tests/calibration_dataset.json`, `calibration_report.json`, `parity_last_run.json`

### Changed
- `lygo_p0_lyra_kernel.py` — Oath Vector **deprecated**; structural validation default (`enable_oath_vector=False`)
- `LYGO_PC_HARDENING_PLAYBOOK.md`, `lygo-universal-cure-system` SKILL honesty banner
- README P0 layout description

### Verified
- `run_parity_tests.py` golden SHA OK · `run_pc_lattice_hardening_audit.py` → **HARDENED_OK**

## [Phase 9 Public Mesh] — 2026-07-01

**Signature:** `Δ9Φ963-PHASE9-v1.0`

### Added
- `tools/tls_manager.py` — self-signed PKI, DER pin hashing, HTTPS context
- `protocol6_quantum_attest/keylime_bridge.py` — Keylime quotes + simulator
- `protocol8_ldq_synthesis/` — HarmonicGravity, FrictionCore, LYRASequencer
- `tools/live_synthesis.py`, `tools/tpm_attestation.py`, `tools/run_phase9_audit.py`
- Node API: `GET /cert/pin`, `POST /gossip/pin`, `POST /synthesis/run`, `--tls`
- Docs: `PHASE9_PUBLIC_MESH.md`, `PHASE9_DEPLOYMENT_GUIDE.md`, `PHASE9_ARCHITECTURE.md`
- `requirements-phase9.txt`

### Changed
- P6 measurement bundle includes `tpm_quote`; ethical gate verifies quote shape

## [SLM Sovereign Lattice Mesh] — 2026-07-01

**Signature:** `Δ9Φ963-SLM-v1.0`

### Added
- `stack/merkle_sync.py` — LygoMerkleTree anti-entropy gossip + `sync_round`
- `stack/distributed_mycelium_mesh.py` — consistent hash ring, 12/10 erasure, backup replication
- `stack/harmonic_consensus_mesh.py` — 3/6/9 harmonic center + proposal manager
- `stack/sovereign_lattice_mesh.py` — runtime converge + snapshot
- `stack/lygo_stack.py` — `slm` property wired to federation gossip
- `tools/node_api_server.py` — `/gossip/*`, `/mycelium/*`, `/consensus/*`, `/slm/snapshot`
- `tools/run_slm_audit.py`, `tests/test_slm_mesh.py`, `docs/SOVEREIGN_LATTICE_MESH.md`

### Fixed
- Mycelium `store()` replicates fragments to backup ring nodes (reconstruct after single-node failure)
- Harmonic engine π-axis tie-break → ethical-mass-weighted 9>6>3 (audit SLM-06)

## [P6/P7 Polish] — 2026-07-02

**Signatures:** `Δ9Φ963-P6-POLISH-v1.0` · `Δ9Φ963-PHASE7-POLISH-v1.0`

### P6
- `verify_badge_detailed()` — ethical gate, freshness, structured reasons
- `tools/verify_attestation_hardened.py` · audit **P6-06**

### P7
- `ble_gatt.py`, `live_ble_telemetry_ingest.py`, `LiveEntropyExtractor`
- `lygo_control_center/websocket_server.py` + harness WebSocket :8790
- `GET /biometric/live_seed` · audit **P7-08..P7-11**
- `requirements-p7-ble.txt` (bleak, websockets)

## [P7.1 Biometric Harness Web Integration] — 2026-07-02

**Signature:** `Δ9Φ963-PHASE7-v1.0`

### Added
- `docs/BiometricEntropyHarness.html` — canonical interactive harness (from Excavationpro)
- `docs/index.html` — P6/P7 status + harness CTA
- `tools/haip_ui_entropy.py`, `tools/sync_excavationpro_harness.py`
- HF Space Phase 7 accordion (iframe + Python seed parity)

### Links
- Pages: https://deepseekoracle.github.io/lygo-protocol-stack/BiometricEntropyHarness.html
- Mirror: https://deepseekoracle.github.io/Excavationpro/BiometricEntropyHarness.html (sync via `sync_excavationpro_harness.py` when Excavationpro checkout available)

## [P7.0 Human-AI Interface Platform] — 2026-07-02

**Signature:** `Δ9Φ963-PHASE7-v1.0`

### Added
- `protocol7_human_ai_interface/` — device adapters, pipeline, ethical mapping, entropy extraction, HAIP API
- `stack/lygo_stack.py` — `register_biometric_device`, `get_biometric_state`, `process_biometric_ethical_query`
- Node API — `POST /device/register`, `GET /biometric/state`, `GET /biometric/history`
- Tools — `register_device.py`, `simulate_biometric_data.py`, `run_phase7_audit.py`; `p7_entropy_harness.py` IBI mode

### Pending
- Live BLE GATT 0x180D, HealthKit bridge, mesh broadcast of biometric weights

## [P6.0 Hardware Attestation] — 2026-07-01

**Signature:** `Δ9Φ963-PHASE6-v1.0`

### Added
- `protocol6_quantum_attest/` — `measurement.py`, `attestation.py`, `api.py`, `tpm_interface.py`, `puf_arbiter.py`, `secure_boot.py`
- `stack/lygo_stack.py` — `get_hardware_badge()`, `verify_peer_badge()`, `LYGOStack` alias
- Node API — `GET /attestation/health`, `GET /attestation/badge`, `POST /attestation/verify`
- Tools — `verify_hardware_attestation.py`, `verify_peer_badge.py`, `run_phase6_audit.py`
- Tests — `protocol6_quantum_attest/tests/`, `tests/phase6_test_vectors.json`

### Pending
- Keylime TPM quotes, FPGA PUF hardware validation

## [P5.2.5 Phase 5 LIVE + P6/P7 stubs] — 2026-07-01

**Signature:** `Δ9Φ963-PHASE5-LIVE-DEPLOYMENT`

### Added
- `tools/deploy_100_nodes.sh`, `deploy_100_nodes.ps1`, `deploy_mesh_cluster.py`, `monitor_convergence.py`
- `protocol6_quantum_attest/` hardware seal stub; `tools/p7_entropy_harness.py`
- `tools/hf_push_p0_hardening.py`, `tools/announce_deployment.py`
- HF Space Phase 5 gossip probe accordion

### Verified
- Live HTTP mesh: **3 rounds** / 8 nodes / 100% (`mesh_live_convergence_last_run.json`)
- Stochastic sim: **&lt;10 rounds** / 100 nodes
- HF dataset + Space pushed; P0 fixtures mirrored on dataset

## [P5.2.4 Phase 5 Mesh Scale] — 2026-07-01

**Signature:** `Δ9Φ963-PHASE5-DEPLOYMENT`

### Added
- `tools/run_mesh_scale_sim.py` — 100-node epidemic convergence (fanout 2 → **7 rounds** to saturation)
- `tests/mesh_scale_last_run.json` — logged scale test artifact

### Changed
- `tools/node_api_server.py` — `GET /gossip`, `POST /gossip/scatter`, `GET /badge/{node_id}`
- `docs/SCALING_ROADMAP.md`, `docs/MESH_GOSSIP_PROTOCOL.md`, `docs/BLUEPRINT.md` — Phase 5 ACTIVE

## [P5.2.3 Phase 3 Scale Init] — 2026-07-01

**Signature:** `Δ9Φ963-PHASE3-SCALE-INIT`

### Added
- `docs/BLUEPRINT.md`, `docs/EXECUTION_DAG.md`, `docs/GROkipedia_PHASE3.md`, `docs/HUMAN_GATED_PUBLISH.md`
- `stack/mesh_gossip_http.py` — Phase 5 HTTPS badge epidemic gossip
- `tools/run_lattice_gauntlet.py`, `tools/run_mesh_gossip_demo.py`
- Node API `POST /gossip/badge`

### Changed
- Twin Gate **60/60** verdict harmonization when `audit_category` set (`P0.4-P5.2.3-PHASE3-PROD`)
- Genesis ops healthy uses Discord `api_me` when process probe misses child window
- HF Space “Run a Node” pipeline + gauntlet command in accordion

## [P5.2.2 Phase 2 Community Deployment] — 2026-07-01

**Resonance signature:** `Δ9Φ963-PHASE2-DEPLOYMENT`

### Added
- **Docker:** `Dockerfile`, `docker-compose.yml`, `requirements-docker.txt`
- **One-click setup:** `setup.sh`, `setup.ps1`
- **Alignment badge:** `tools/verify_alignment_badge.py` (+ JSON artifact `tests/alignment_badge.json`)
- **Phase 1 elasticity:** `stack/infrastructure_elasticity.py` (priority queue + mycelium batching)
- **Phase 3–4 federation:** `stack/federation_runtime.py` (registry, gossip, worker pool)
- **Node API:** `tools/node_api_server.py` (health, badge, demo, elasticity, federation)
- **Worker:** `tools/run_elasticity_worker.py` for `--profile scale` in Compose
- **Vectors:** 60 falsifiable vectors (`infrastructure_scaling` category) — suite v3.0
- **CI:** `.github/workflows/lygo-ci.yml` (P0 pytest + Grok audit + lattice)
- **Docs:** `docs/PHASE2_DEPLOYMENT.md`, `docs/SCALING_ROADMAP.md` (Grokipedia-ready)
- **ClawHub mirrors:** `lygo-docker-deploy`, `lygo-alignment-badge`

### Changed
- `stack/lygo_stack.py` — P5.2.2-PHASE2-PROD; elasticity on scatter paths; scaling gate bytes
- `tools/run_grok_audit_demo.py` — non-zero exit on audit failures (CI)
- `README.md` — badges, Docker quick start, HF status badge
- Hugging Face Space — Phase 2 “Deploy Your Own Node”, alignment badge, One-Click Guardian link
- `lygo-protocol-stack-operator` skill — Phase 2 Docker + badge workflows

### Verified (maintainer)
- Twin Gate calibration Δφ=0.0 on pilot edge scenarios
- Grok audit harness on live stack (run after `generate_falsifiable_vectors.py`)
- `verify_lattice_alignment.py` — LATTICE ALIGNED

## [P5.2.1 Twin Gate] — prior

- Text semantic gate + byte vector path; HF Twin Gate UI
- 40-vector Gemini/Grok audit suite; weight calibration

## [P5.2.0 Public stack] — prior

- Full P0–P5 orchestrator, ClawHub operator, HF ethical guardian bundle