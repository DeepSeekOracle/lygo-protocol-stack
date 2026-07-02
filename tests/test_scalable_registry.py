"""Scalable registry — CDC, hierarchical manifest, retrieve, verify."""

from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "tools"))

from scalable_registry.chunking import content_defined_chunks, write_chunk_to_cas  # noqa: E402
from scalable_registry.manifest_builder import (  # noqa: E402
    _json_len,
    _leaf_manifest,
    build_manifest_from_bytes,
    build_manifest_from_hashes,
    expand_chunk_hashes,
    manifest_content_sha256,
)
from scalable_registry.merkle import merkle_root  # noqa: E402
from scalable_registry.registry_manager import CAS_ROOT, add_manifest_entry, persist_manifest  # noqa: E402
from scalable_registry.retrieve import verify_and_stream_to_file  # noqa: E402
from scalable_registry.verify import run_full_verify  # noqa: E402


@pytest.fixture()
def cas_tmp(tmp_path, monkeypatch):
    cas = tmp_path / "cas"
    cas.mkdir()
    reg = tmp_path / "scalable_registry"
    reg.mkdir()
    manifests = reg / "manifests"
    manifests.mkdir()
    monkeypatch.setattr("scalable_registry.registry_manager.CAS_ROOT", cas)
    monkeypatch.setattr("scalable_registry.registry_manager.REGISTRY_DIR", reg)
    monkeypatch.setattr("scalable_registry.registry_manager.REGISTRY_FILE", reg / "registry.json")
    monkeypatch.setattr("scalable_registry.registry_manager.MANIFESTS_DIR", manifests)
    monkeypatch.setattr("scalable_registry.retrieve.CAS_ROOT", cas)
    return cas


def test_cdc_deterministic():
    data = secrets.token_bytes(200_000)
    a = content_defined_chunks(data, min_size=8 * 1024, avg_size=16 * 1024, max_size=32 * 1024)
    b = content_defined_chunks(data, min_size=8 * 1024, avg_size=16 * 1024, max_size=32 * 1024)
    assert a == b
    assert len(a) > 1


def test_hierarchical_manifest_under_limit(cas_tmp):
    # Many tiny chunks → forces sub-manifests
    hashes = []
    for _ in range(2000):
        chunk = secrets.token_bytes(256)
        hashes.append(write_chunk_to_cas(chunk, cas_tmp))
    manifest = build_manifest_from_hashes(
        hashes,
        {"name": "hier-test", "version": "1"},
        size_bytes=2000 * 256,
        node_id="TEST_NODE",
        require_p6=False,
    )
    assert manifest["type"] == "super_manifest"
    from scalable_registry import MAX_MANIFEST_JSON_BYTES

    assert _json_len(manifest) <= MAX_MANIFEST_JSON_BYTES
    expanded = expand_chunk_hashes(manifest)
    assert len(expanded) == 2000


def test_register_retrieve_roundtrip(cas_tmp, tmp_path):
    payload = secrets.token_bytes(50_000)
    manifest = build_manifest_from_bytes(
        payload,
        {"name": "roundtrip"},
        cas_tmp,
        node_id="TEST_NODE",
        require_p6=False,
    )
    manifest["content_sha256"] = manifest_content_sha256(manifest)
    persist_manifest(manifest)
    add_manifest_entry(
        manifest["manifest_id"],
        manifest["merkle_root"],
        content_sha256=manifest["content_sha256"],
        metadata={"name": "roundtrip"},
    )
    out = tmp_path / "out.bin"
    verify_and_stream_to_file(manifest, out, cas_root=cas_tmp)
    assert out.read_bytes() == payload


def test_verify_registry_aligned(cas_tmp):
    report = run_full_verify(write_artifact=False)
    assert report["verdict"] in ("ALIGNED", "QUARANTINE")