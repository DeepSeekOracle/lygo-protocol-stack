#!/usr/bin/env python3
"""Compat entry — LYGO USB supervisor (same process as BUILDR daemon)."""

from __future__ import annotations

from buildr_usb_daemon import main

if __name__ == "__main__":
    raise SystemExit(main())