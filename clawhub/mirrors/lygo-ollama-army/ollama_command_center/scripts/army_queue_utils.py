#!/usr/bin/env python3
"""Shared army queue hygiene: dedupe, stale locks, depth counts."""

from __future__ import annotations

import json
import time
from pathlib import Path


def queue_dirs(cc: Path, army: Path | None = None) -> list[Path]:
    dirs: list[Path] = []
    tasks = cc / "tasks"
    if tasks.is_dir():
        dirs.append(tasks)
    if army is not None:
        legacy = army / "ollama_queue"
        if legacy.is_dir():
            dirs.append(legacy)
    return dirs


def iter_task_files(dirs: list[Path], *, include_locks: bool = True) -> list[Path]:
    out: list[Path] = []
    for d in dirs:
        out.extend(sorted(d.glob("*.task.json")))
        if include_locks:
            out.extend(sorted(d.glob("*.lock")))
    return out


def read_task_role(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("role") or "general")
    except (OSError, json.JSONDecodeError):
        return None


def pending_roles(dirs: list[Path]) -> set[str]:
    roles: set[str] = set()
    for p in iter_task_files(dirs):
        role = read_task_role(p)
        if role:
            roles.add(role)
    return roles


def unique_task_count(dirs: list[Path]) -> int:
    """Count tasks once by filename (tasks/ and legacy queue may mirror)."""
    seen: set[str] = set()
    for d in dirs:
        for p in d.glob("*.task.json"):
            seen.add(p.name)
        for p in d.glob("*.lock"):
            seen.add(f"{p.stem}.task.json")
    return len(seen)


def cleanup_stale_locks(dirs: list[Path], max_age_seconds: float = 600) -> int:
    restored = 0
    now = time.time()
    for d in dirs:
        for lock in list(d.glob("*.lock")):
            try:
                age = now - lock.stat().st_mtime
                if age <= max_age_seconds:
                    continue
                task_path = d / f"{lock.stem}.task.json"
                lock.replace(task_path)
                restored += 1
            except OSError:
                lock.unlink(missing_ok=True)
                restored += 1
    return restored


def dedupe_by_role(
    dirs: list[Path],
    *,
    keep_newest: bool = True,
    max_per_role: int = 1,
    glob_pattern: str = "*.task.json",
) -> int:
    """Keep at most max_per_role pending tasks per role across all queue dirs."""
    by_role: dict[str, list[Path]] = {}
    for d in dirs:
        for p in d.glob(glob_pattern):
            role = read_task_role(p)
            if not role:
                continue
            by_role.setdefault(role, []).append(p)

    removed = 0
    for paths in by_role.values():
        if len(paths) <= max_per_role:
            continue
        paths.sort(key=lambda p: p.stat().st_mtime, reverse=keep_newest)
        for p in paths[max_per_role:]:
            p.unlink(missing_ok=True)
            removed += 1
    return removed


def dedupe_cron_by_role(dirs: list[Path], *, keep_newest: bool = True) -> int:
    """Keep at most one pending cron-* task per role across all queue dirs."""
    return dedupe_by_role(dirs, keep_newest=keep_newest, max_per_role=1, glob_pattern="cron-*.task.json")


def probe_tcp_port(host: str, port: int, timeout: float = 3.0) -> bool:
    import socket

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_http_ok(url: str, timeout: float = 5.0) -> bool:
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LYGO-Army-Health/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except (urllib.error.URLError, OSError, ValueError):
        return False