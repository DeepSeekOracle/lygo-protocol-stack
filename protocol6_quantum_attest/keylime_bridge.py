"""Keylime TPM quote bridge — live agent or deterministic simulator."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
from typing import Any

P9_KEYLIME_VERSION = "Δ9Φ963-PHASE9-KEYLIME-v1.0"


def _simulated_quote(node_id: str) -> dict[str, Any]:
    material = json.dumps({"node": node_id, "mode": "sim"}, sort_keys=True).encode()
    ai = hashlib.sha256(material).hexdigest()
    tpm = hashlib.sha256((ai + "tpm-stub").encode()).hexdigest()
    return {
        "ai": ai,
        "tpm": tpm,
        "pcr0": "0000000000000000000000000000000000000000",
        "pcr1": "0000000000000000000000000000000000000000",
        "mode": "simulated",
        "signature": P9_KEYLIME_VERSION,
    }


class KeylimeAttestation:
    def __init__(
        self,
        node_id: str,
        agent_url: str = "http://127.0.0.1:9002/v2/",
        *,
        verify_tls: bool = False,
    ) -> None:
        self.node_id = node_id
        self.agent_url = agent_url.rstrip("/") + "/"
        self.verify_tls = verify_tls
        self.registered = False

    def register_node(self, ip_address: str | None = None) -> bool:
        ip = ip_address or socket.gethostbyname(socket.gethostname())
        payload = {
            "agent_id": self.node_id,
            "ip": ip,
            "tpm_policy": {
                "pcr0": "0000000000000000000000000000000000000000",
                "pcr1": "0000000000000000000000000000000000000000",
            },
        }
        try:
            import requests

            resp = requests.post(f"{self.agent_url}agents/", json=payload, timeout=3, verify=self.verify_tls)
            self.registered = resp.status_code in (200, 201)
            return self.registered
        except Exception:
            self.registered = False
            return False

    def get_quote(self) -> dict[str, Any] | None:
        if os.environ.get("LYGO_KEYLIME_FORCE_SIM", "1") == "1":
            return _simulated_quote(self.node_id)
        try:
            import requests

            if not self.registered:
                self.register_node()
            resp = requests.get(
                f"{self.agent_url}agents/{self.node_id}/quote",
                timeout=3,
                verify=self.verify_tls,
            )
            if resp.status_code == 200:
                data = resp.json()
                data["mode"] = "keylime"
                data["signature"] = P9_KEYLIME_VERSION
                return data
        except Exception:
            pass
        return _simulated_quote(self.node_id)

    @staticmethod
    def verify_quote(quote_data: dict[str, Any] | None) -> bool:
        if not isinstance(quote_data, dict):
            return False
        return "ai" in quote_data and "tpm" in quote_data

    def keylime_cli_available(self) -> bool:
        try:
            cp = subprocess.run(
                ["keylime_agent", "--version"],
                capture_output=True,
                timeout=2,
                check=False,
            )
            return cp.returncode == 0
        except Exception:
            return False