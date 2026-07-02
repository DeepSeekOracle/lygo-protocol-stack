#!/usr/bin/env python3
"""LYGO Phase 9 — TLS manager: self-signed PKI, pinning, rotation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

P9_TLS_VERSION = "Δ9Φ963-PHASE9-TLS-v1.0"


class TLSCertificateManager:
    def __init__(self, node_id: str, cert_dir: str | Path = "certs") -> None:
        self.node_id = node_id
        self.cert_dir = Path(cert_dir)
        self.cert_file = self.cert_dir / f"{node_id}.crt"
        self.key_file = self.cert_dir / f"{node_id}.key"
        self.pin_file = self.cert_dir / "pins.json"
        self.pins: dict[str, Any] = self._load_pins()
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def _load_pins(self) -> dict[str, Any]:
        if self.pin_file.is_file():
            return json.loads(self.pin_file.read_text(encoding="utf-8"))
        return {}

    def _save_pins(self) -> None:
        self.pin_file.write_text(json.dumps(self.pins, indent=2), encoding="utf-8")

    @staticmethod
    def cert_pin(cert_bytes: bytes, *, encoding: str = "pem") -> str:
        if encoding == "pem":
            try:
                cert = x509.load_pem_x509_certificate(cert_bytes)
                cert_bytes = cert.public_bytes(serialization.Encoding.DER)
            except Exception:
                pass
        return hashlib.sha256(cert_bytes).hexdigest()

    def generate_self_signed(self, validity_days: int = 30) -> str:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = datetime.now(timezone.utc)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, self.node_id),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LYGO Mesh"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=validity_days))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .sign(key, hashes.SHA256())
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self.cert_file.write_bytes(cert_pem)
        self.key_file.write_bytes(key_pem)
        pin = self.cert_pin(cert.public_bytes(serialization.Encoding.DER), encoding="der")
        expiry = (now + timedelta(days=validity_days)).isoformat()
        self.pins[self.node_id] = {"pin": pin, "expiry": expiry, "signature": P9_TLS_VERSION}
        self._save_pins()
        return pin

    def get_pin(self, node_id: str | None = None) -> str | None:
        nid = node_id or self.node_id
        entry = self.pins.get(nid)
        return str(entry.get("pin")) if isinstance(entry, dict) else None

    def ingest_peer_pin(self, node_id: str, pin: str, expiry: str | None = None) -> dict[str, Any]:
        self.pins[node_id] = {
            "pin": pin,
            "expiry": expiry or "",
            "signature": P9_TLS_VERSION,
        }
        self._save_pins()
        return {"ok": True, "node_id": node_id, "pin": pin}

    def verify_peer_cert_bytes(self, cert_data: bytes) -> str | None:
        pin = self.cert_pin(cert_data)
        for nid, info in self.pins.items():
            if isinstance(info, dict) and info.get("pin") == pin:
                return nid
        return None

    def verify_peer(self, peer_cert_file: str | Path) -> str | None:
        data = Path(peer_cert_file).read_bytes()
        return self.verify_peer_cert_bytes(data)

    def rotate(self, node_id: str | None = None) -> str:
        _ = node_id or self.node_id
        return self.generate_self_signed()

    def ssl_server_context(self) -> ssl.SSLContext:
        if not self.cert_file.is_file() or not self.key_file.is_file():
            self.generate_self_signed()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(certfile=str(self.cert_file), keyfile=str(self.key_file))
        return ctx

    def pin_payload(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "pin": self.get_pin(self.node_id),
            "expiry": (self.pins.get(self.node_id) or {}).get("expiry"),
            "signature": P9_TLS_VERSION,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="LYGO Phase 9 TLS manager")
    ap.add_argument("--node-id", default=os.environ.get("LYGO_NODE_ID", "LYGO_NODE"))
    ap.add_argument("--cert-dir", default="certs")
    ap.add_argument("--generate", action="store_true", help="Generate/rotate self-signed cert")
    args = ap.parse_args()
    mgr = TLSCertificateManager(args.node_id, args.cert_dir)
    if args.generate or not mgr.cert_file.is_file():
        pin = mgr.generate_self_signed()
        print(json.dumps({"ok": True, "pin": pin, **mgr.pin_payload()}, indent=2))
    else:
        print(json.dumps(mgr.pin_payload(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())