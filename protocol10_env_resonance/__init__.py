"""Protocol 10 — Environmental Resonance Bridge (ERB).

Turns radio-physics measurements of a *place* into deterministic lattice
cells: WiFi Channel State Information (CSI) in, P0-gated, P1-anchored,
verifiable environmental memory out.

Pipeline (all deterministic for a given input stream):

    CSI frames (ESP32-S3 / research NIC, or the synthetic generator)
        -> csi_core     band energies + breathing rate (physics, no learned model)
        -> lattice_cell fixed-point quantisation -> canonical bytes -> SHA-256
        -> P0           byte-entropy gate (AMPLIFY / SOFTEN / QUARANTINE)
        -> P1           Memory Mycelium scatter (indestructible environmental memory)
        -> P8           anchor integer -> harmonic parameters (room resonance)

Public API:

    from protocol10_env_resonance import (
        EnvResonanceLattice, LatticeCell, CSIFrame,
        synthesize_csi, estimate_breathing, motion_energy_db,
    )

Credit: the sensing physics follows the open WiFi-CSI line of work —
ruvnet/RuView (MIT), ESPectre, ESP32-CSI-Tool, and IEEE 802.11bf WLAN
Sensing. This module is the LYGO adaptation: deterministic anchoring, not
pose estimation. See README.md for what is real and what is not.
"""

from .csi_core import (
    BREATH_BAND_HZ,
    CSIFrame,
    DRIFT_THRESHOLD,
    FINGERPRINT_LEVELS,
    BreathEstimate,
    band_energy_db,
    channel_fingerprint,
    estimate_breathing,
    estimate_heart_rate,
    fingerprint_distance,
    motion_energy_db,
    parse_esp32_csv_row,
    prepare_window,
)
from .lattice_cell import (
    ERB_VERSION,
    LatticeCell,
    canonical_bytes,
    quantize_features,
)
from .bridge import EnvResonanceLattice, resonance_parameters
from .synthetic import synthesize_csi

__all__ = [
    "BREATH_BAND_HZ",
    "CSIFrame",
    "DRIFT_THRESHOLD",
    "FINGERPRINT_LEVELS",
    "BreathEstimate",
    "ERB_VERSION",
    "EnvResonanceLattice",
    "LatticeCell",
    "band_energy_db",
    "canonical_bytes",
    "channel_fingerprint",
    "estimate_breathing",
    "estimate_heart_rate",
    "fingerprint_distance",
    "motion_energy_db",
    "parse_esp32_csv_row",
    "prepare_window",
    "quantize_features",
    "resonance_parameters",
    "synthesize_csi",
]
__version__ = ERB_VERSION
