"""BLE Heart Rate GATT 0x180D / 0x2A37 — RR-interval (IBI) extraction."""

from __future__ import annotations

import struct
from typing import Any

HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


def parse_heart_rate_measurement(data: bytes) -> dict[str, Any]:
    """Parse Bluetooth Heart Rate Measurement characteristic (0x2A37)."""
    if len(data) < 2:
        return {"heart_rate": None, "ibi_ms": [], "raw_len": len(data)}

    flags = data[0]
    hr_16bit = flags & 0x01
    contact_supported = (flags & 0x02) >> 1
    contact_detected = (flags & 0x04) >> 2
    energy_expended = (flags & 0x08) >> 3
    rr_present = (flags & 0x10) >> 4

    offset = 1
    if hr_16bit:
        heart_rate = struct.unpack_from("<H", data, offset)[0]
        offset += 2
    else:
        heart_rate = data[offset]
        offset += 1

    if energy_expended:
        offset += 2

    ibi_ms: list[int] = []
    if rr_present:
        while offset + 1 < len(data):
            rr_raw = struct.unpack_from("<H", data, offset)[0]
            ibi_ms.append(int((rr_raw / 1024.0) * 1000))
            offset += 2

    return {
        "heart_rate": heart_rate,
        "ibi_ms": ibi_ms,
        "contact_supported": bool(contact_supported),
        "contact_detected": bool(contact_detected),
        "flags": flags,
    }


def bleak_available() -> bool:
    try:
        import bleak  # noqa: F401

        return True
    except ImportError:
        return False