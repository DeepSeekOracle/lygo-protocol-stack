# Phase 9 Deployment Guide

## 1. Dependencies

```bash
pip install -r requirements-phase9.txt
pip install -r requirements-p7-ble.txt   # optional BLE ingest
```

## 2. Certificates

```bash
set LYGO_NODE_ID=NODE_A
python tools/tls_manager.py --generate --cert-dir certs/NODE_A
```

## 3. Node API (HTTP or HTTPS)

```bash
python tools/node_api_server.py --host 0.0.0.0 --port 8787
python tools/node_api_server.py --tls --port 8443 --cert-dir certs/NODE_A
```

## 4. Pin gossip (two nodes)

```bash
curl -s http://127.0.0.1:8787/cert/pin
curl -X POST http://127.0.0.1:8788/gossip/pin -H "Content-Type: application/json" ^
  -d "{\"node_id\":\"NODE_A\",\"pin\":\"<pin>\",\"expiry\":\"...\"}"
```

## 5. Keylime (optional)

```bash
python tools/tpm_attestation.py --register --node-id NODE_A
python tools/tpm_attestation.py --quote
```

## 6. Live synthesis

```bash
python tools/live_ble_telemetry_ingest.py   # optional: refresh latest_seed.json
python tools/live_synthesis.py --duration 10
curl -X POST http://127.0.0.1:8787/synthesis/run -H "Content-Type: application/json" -d "{}"
```

## 7. Audit gate

```bash
python tools/run_phase9_audit.py
python tools/verify_lattice_alignment.py
```