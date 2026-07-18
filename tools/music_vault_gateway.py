#!/usr/bin/env python3
"""Local-only gateway to serve CAS vault objects by SHA-256. Default bind 127.0.0.1."""
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

DEFAULT_VAULT = Path(r"I:\E Drive\MUSIC_VAULT")
STACK_MANIFEST = Path(__file__).resolve().parents[1] / "data" / "music_catalog" / "music_vault_manifest.json"


def load_index(vault: Path) -> dict[str, dict]:
    # prefer full index for paths
    full = vault / "manifest" / "vault_index.json"
    pub = STACK_MANIFEST
    path = full if full.exists() else pub
    data = json.loads(path.read_text(encoding="utf-8"))
    by = {}
    for o in data.get("objects") or []:
        by[o["sha256"]] = o
    return by, data


class Handler(BaseHTTPRequestHandler):
    vault: Path = DEFAULT_VAULT
    by_hash: dict = {}
    manifest: dict = {}

    def log_message(self, fmt, *args):
        print("[gw]", fmt % args)

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path in ("/", "/index", "/manifest"):
            body = json.dumps(
                {
                    "signature": self.manifest.get("signature"),
                    "merkle_root": self.manifest.get("merkle_root"),
                    "stats": self.manifest.get("stats"),
                    "objects": len(self.by_hash),
                    "usage": "/sha256/<hex> or /cas/<rel>",
                },
                indent=2,
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path.startswith("/sha256/"):
            digest = path[len("/sha256/") :].strip().lower()
            row = self.by_hash.get(digest)
            if not row:
                self.send_error(404, "unknown hash")
                return
            # try CAS then original paths
            candidates = []
            if row.get("cas_path"):
                candidates.append(self.vault / "cas" / row["cas_path"])
            # rebuild cas path from digest
            ext = row.get("ext") or ".wav"
            candidates.append(self.vault / "cas" / digest[:2] / f"{digest}{ext}")
            for p in row.get("paths") or []:
                candidates.append(Path(p))
            for c in candidates:
                if c and Path(c).is_file():
                    return self._file(Path(c))
            self.send_error(404, "file not on this machine")
            return
        if path.startswith("/cas/"):
            rel = path[len("/cas/") :]
            fp = self.vault / "cas" / rel
            if fp.is_file():
                return self._file(fp)
            self.send_error(404, "not found")
            return
        self.send_error(404, "try / or /sha256/<hash>")

    def _file(self, fp: Path):
        data = fp.read_bytes()
        ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-SHA256", fp.name.split(".")[0] if len(fp.stem) == 64 else "")
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--host", default="127.0.0.1", help="Use 127.0.0.1 only unless you intentionally expose")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    by, man = load_index(args.vault)
    Handler.vault = args.vault
    Handler.by_hash = by
    Handler.manifest = man
    print(f"Sovereign vault gateway on http://{args.host}:{args.port}/  objects={len(by)}")
    print("Ctrl+C to stop. Audio is served only if CAS or original paths exist.")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
