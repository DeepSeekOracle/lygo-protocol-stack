#!/usr/bin/env python3
"""Phase 9 audit — TLS pinning, TPM quote, live synthesis."""

from __future__ import annotations

import json
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

P9_VERSION = "Δ9Φ963-PHASE9-v1.0"


def main() -> int:
    from protocol6_quantum_attest.keylime_bridge import KeylimeAttestation
    from tls_manager import TLSCertificateManager
    from live_synthesis import generate_audio_from_seed

    results: list[dict] = []
    t0 = time.perf_counter()
    td = Path(tempfile.mkdtemp())

    mgr_a = TLSCertificateManager("node_a", td / "certs_a")
    pin_a = mgr_a.generate_self_signed()
    results.append(
        {
            "id": "P9-01",
            "pass": mgr_a.cert_file.is_file() and mgr_a.key_file.is_file(),
            "detail": "self-signed cert+key",
        }
    )

    mgr_b = TLSCertificateManager("node_b", td / "certs_b")
    pin_b = mgr_b.generate_self_signed()
    mgr_a.ingest_peer_pin("node_b", pin_b)
    mgr_b.ingest_peer_pin("node_a", pin_a)
    results.append(
        {
            "id": "P9-02",
            "pass": mgr_a.get_pin("node_b") == pin_b and mgr_b.get_pin("node_a") == pin_a,
        }
    )

    peer_id = mgr_a.verify_peer(mgr_b.cert_file)
    tls_handshake_ok = False
    if peer_id == "node_b":
        port = 18443

        class _H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *args):
                return

        httpd = HTTPServer(("127.0.0.1", port), _H)
        ctx = mgr_b.ssl_server_context()
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

        def _serve():
            httpd.handle_request()

        th = threading.Thread(target=_serve, daemon=True)
        th.start()
        time.sleep(0.2)
        try:
            raw = socket.create_connection(("127.0.0.1", port), timeout=3)
            client_ctx = ssl.create_default_context()
            client_ctx.check_hostname = False
            client_ctx.verify_mode = ssl.CERT_NONE
            with client_ctx.wrap_socket(raw, server_hostname="node_b") as ss:
                cert_bin = ss.getpeercert(binary_form=True)
                if cert_bin:
                    tls_handshake_ok = mgr_a.verify_peer_cert_bytes(cert_bin) == "node_b"
        except Exception:
            tls_handshake_ok = False
        finally:
            try:
                httpd.server_close()
            except Exception:
                pass

    results.append({"id": "P9-03", "pass": tls_handshake_ok and peer_id == "node_b"})

    kl = KeylimeAttestation("audit_node")
    quote = kl.get_quote()
    results.append(
        {
            "id": "P9-04",
            "pass": quote is not None and KeylimeAttestation.verify_quote(quote),
            "mode": (quote or {}).get("mode"),
        }
    )

    wav = td / "p9_test.wav"
    synth = generate_audio_from_seed("7e8d18fda979cbef", wav, duration_sec=1.0)
    wav_ok = wav.is_file() and wav.stat().st_size > 44 and synth.get("samples", 0) > 0
    results.append({"id": "P9-05", "pass": wav_ok, "bytes": wav.stat().st_size if wav.is_file() else 0})

    for script in ("tls_manager.py", "tpm_attestation.py", "live_synthesis.py"):
        cp = subprocess.run(
            [sys.executable, str(ROOT / "tools" / script), "--help"],
            cwd=ROOT,
            capture_output=True,
            timeout=30,
        )
        results.append({"id": f"P9-CLI-{script}", "pass": cp.returncode == 0})

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    all_pass = all(r["pass"] for r in results)
    report = {
        "signature": P9_VERSION,
        "vectors": results,
        "all_pass": all_pass,
        "duration_ms": elapsed_ms,
    }
    out = ROOT / "tests" / "phase9_audit_last_run.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())