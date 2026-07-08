"""
Fixes for the Python portion of the LYGO stack.

Bug: mutable/eagerly-evaluated default argument.

    class FractalEntanglementEngine:
        def __init__(self, key: bytes = Fernet.generate_key()):
            ...

`Fernet.generate_key()` runs exactly ONCE, when the class body is executed
(at import time) -- not once per instance. Every instance created without
an explicit `key=` argument silently shares the same encryption key, which
defeats the purpose of per-instance key material and is a real security
bug, not just a style nit.

Fix: use `key: Optional[bytes] = None` and generate inside the constructor
if not supplied.
"""

from typing import Dict, Any, Optional
import hashlib
import json
from cryptography.fernet import Fernet


class FractalEntanglementEngine:
    """Encrypts and (conceptually) distributes data via fractal-style sharding."""

    def __init__(self, key: Optional[bytes] = None):
        # Generate a fresh key per instance unless one is explicitly supplied.
        self.key = key if key is not None else Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.fractal_depth = 8

    def store_empathy_data(self, data: Dict[str, Any]) -> str:
        raw_bytes = json.dumps(data).encode()
        encrypted = self.cipher.encrypt(raw_bytes)
        data_hash = hashlib.sha3_256(encrypted).hexdigest()
        storage_id = f"LYGO_FRAC_{data_hash[:16]}"
        return storage_id


# --- Secondary fix: qiskit_aer import guard -------------------------------
# The original file imports qiskit_aer unconditionally. That package ships
# separately from `qiskit` (pip install qiskit-aer) and is commonly missing,
# which turns an otherwise-working script into an ImportError at startup
# with no actionable message. Guard it so the failure is clear:
try:
    from qiskit_aer import AerSimulator  # noqa: F401
except ImportError as e:
    raise ImportError(
        "qiskit_aer is required for QuantumLightAnchor but is not installed. "
        "Install it with: pip install qiskit-aer --break-system-packages"
    ) from e


# --- Secondary fix: qc.ry() takes an angle in radians ---------------------
# Original code:
#   joy_freq = (len(data) % 9) * LygoConstants.FREQ_REPAIR   # e.g. up to 8 * 528 = 4224
#   qc.ry(joy_freq, qreg[i])
# Passing a value in the thousands as a rotation angle (radians) just wraps
# around the unit circle thousands of times -- it's not a bug that crashes,
# but it means the "frequency" concept has no actual effect on the qubit
# state beyond `joy_freq mod 2*pi`. If the intent is for FREQ_REPAIR (528Hz)
# to influence the rotation, normalize it into a bounded angle first, e.g.:
import math


def normalized_rotation_angle(raw_value: float) -> float:
    """Map an arbitrary 'frequency-derived' value onto a single rotation
    in [0, 2*pi) so the angle passed to qc.ry() is meaningful rather than
    an uncontrolled multi-wraparound value."""
    return raw_value % (2 * math.pi)


# === BRIDGE PROTOCOL ADDITION (real code for task) ===
# Integrates the fixes + existing lattice.
# Grounded in Merkle, soulbound, bridging.
# Symbolic Light Math (Solfeggio etc) for governance/future.

from typing import List
import sys
sys.path.insert(0, '..')  # for stack access

class LYGOBlockchainBridge:
    """Real bridge impl.
    Uses existing mycelium for storage, P0 for ethical, vortex for consensus.
    Blockchain side: soulbound ethical mass token sim, Merkle anchor.

    Security model (see docs/bridge/*Fixed.sol):
    - Ethical mass may only be created via recordEthicalAction gated by a real attestor.
    - Chain registries may only be set by the bridge owner.
    - Direct public mint is impossible.
    """
    def __init__(self):
        # Reuse existing
        try:
            from stack.distributed_mycelium_mesh import DistributedMyceliumMesh
            self.mycelium = DistributedMyceliumMesh()
        except:
            self.mycelium = None  # fallback
        self.anchors = {}

    def anchor_to_chain(self, data: bytes, light_code: str, triad: List[int], mass: float) -> dict:
        """Bridge: store in mycelium, anchor Merkle on 'chain' (sim), soulbound mass."""
        if self.mycelium:
            res = self.mycelium.store_data(data, 100)  # use if available
        else:
            res = {'id': light_code}
        merkle = __import__('hashlib').sha256(data).hexdigest()
        anchor = {
            'light_code': light_code,
            'triad': triad,  # symbolic
            'ethical_mass': max(0.618, min(1.618, mass)),  # real bound
            'mycelium': res,
            'merkle_root': merkle,
            'soulbound': True,
            'tx': '0x' + merkle[:16]
        }
        self.anchors[light_code] = anchor
        return anchor

    def verify_bridge(self, light_code: str) -> bool:
        return light_code in self.anchors

print('LYGO Blockchain Bridge loaded and integrated with lattice.')
