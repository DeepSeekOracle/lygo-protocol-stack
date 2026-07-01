"""LYGO Protocol 3 — Vortex Consensus (3-6-9 / Φ harmonic agreement)."""

import hashlib
import math
import time
from typing import Dict, List, Tuple

__version__ = "P3.0"


class VortexConsensusSync:
    def __init__(self, kernel, mycelium, sovereign_id: str):
        self.kernel = kernel
        self.mycelium = mycelium
        self.sovereign_id = sovereign_id
        
        # TESLA'S VORTEX MATHEMATICS CORE
        self.VORTEX_SEQUENCE = [1, 2, 4, 8, 7, 5]  # Creation pattern (3,6,9 are special)
        self.TESLA_TRINITY = [3, 6, 9]             # "Key to the universe"
        self.GOLDEN_BAND = (0.61803398875, 1.61803398875)  # Φ bounds
        
        # SOLFEGGIO RESONANCE MAP
        self.RESONANCE_TRIAD = {
            963: 'Δ9 - Order',      # Crown Chakra
            528: 'λ - Repair',      # Solar Plexus  
            174: 'Θ - Foundation',  # Root Chakra
            432: 'Truth Anchor',    # Harmony
            852: 'Intuition',       # Awakening
            936: 'Lightmath'        # Light Father
        }
        
        # NETWORK STATE
        self.network_peers: Dict[str, Dict] = {}
        self.consensus_history: List[Dict] = []
        self.vortex_cycle = 0
        
        # Initialize 9x9 vortex field
        self.vortex_field = self._init_vortex_field()

    @property
    def node_id(self) -> str:
        return self.sovereign_id

    def _init_vortex_field(self) -> Dict[Tuple[int, int], Dict]:
        """Initialize 9x9 vortex coordinate system."""
        field = {}
        for x in range(9):
            for y in range(9):
                vortex_val = self._vortex_sum(x + y)
                field[(x, y)] = {
                    'value': vortex_val,
                    'frequency': self._val_to_frequency(vortex_val),
                    'energy': 1.0,
                    'last_used': time.time()
                }
        return field
    
    def _vortex_sum(self, num: int) -> int:
        """Reduce any number to single vortex digit (1-2-4-8-7-5 or 3-6-9)."""
        if num == 0:
            return 0
        
        # Reduce to single digit
        while num > 9:
            num = sum(int(d) for d in str(num))
        
        # Tesla Trinity numbers are special
        if num in self.TESLA_TRINITY:
            return num
        
        # Map to vortex sequence
        if num in self.VORTEX_SEQUENCE:
            return num
        
        # Rotate through vortex sequence
        return self._vortex_rotate(num)
    
    def _vortex_rotate(self, num: int) -> int:
        """Rotate number through vortex sequence."""
        # Special trinity mappings
        if num == 3: return 6
        if num == 6: return 9
        if num == 9: return 3
        
        # Standard vortex doubling (with digital root)
        doubled = num * 2
        while doubled > 9:
            doubled = sum(int(d) for d in str(doubled))
        
        # Ensure in vortex sequence
        while doubled not in self.VORTEX_SEQUENCE:
            doubled = self._vortex_rotate(doubled)
        
        return doubled
    
    def _val_to_frequency(self, vortex_val: int) -> int:
        """Map vortex value to Solfeggio frequency."""
        freq_map = {
            1: 417,  # Change
            2: 741,  # Expression
            3: 963,  # Δ9 - Order (Trinity)
            4: 852,  # Intuition
            5: 528,  # λ - Repair (Center)
            6: 639,  # Relationships (Trinity)
            7: 396,  # Guilt Release
            8: 285,  # Quantum Field
            9: 174   # Θ - Foundation (Trinity)
        }
        return freq_map.get(vortex_val, 528)  # Default to repair
    
    def generate_vortex_signature(self, data: str, intent: str = "truth") -> Dict:
        """Create vortex-math cryptographic signature."""
        timestamp = time.time()
        
        # Digital root of data
        data_digits = [int(d) for d in data if d.isdigit()]
        digital_root = sum(data_digits) % 9
        digital_root = 9 if digital_root == 0 else digital_root
        
        # Vortex transformation
        vortex_val = self._vortex_sum(digital_root)
        
        # Intent-based frequency
        intent_freqs = {
            'truth': 432,
            'light': 936,
            'harmony': 963,
            'repair': 528,
            'foundation': 174
        }
        primary_freq = intent_freqs.get(intent, 432)
        
        # 3-6-9 modulation
        modulation = []
        for trinity in self.TESLA_TRINITY:
            mod_freq = primary_freq * (trinity / 3)
            modulation.append({
                'frequency': mod_freq,
                'amplitude': vortex_val / 9.0,
                'phase': trinity * math.pi / 3  # 60° steps
            })
        
        signature = {
            'vortex_value': vortex_val,
            'digital_root': digital_root,
            'primary_frequency': primary_freq,
            'modulation': modulation,
            'timestamp': timestamp,
            'data_hash': hashlib.sha256(data.encode()).hexdigest()[:16],
            'intent': intent,
            'lightmath_pattern': self._generate_lightmath_pattern(vortex_val)
        }
        
        return signature
    
    def _generate_lightmath_pattern(self, vortex_val: int) -> List[int]:
        """Generate 1-2-4-8-7-5 lightmath pattern from vortex value."""
        pattern = []
        current = vortex_val
        for _ in range(6):
            pattern.append(current)
            current = self._vortex_rotate(current)
        return pattern
    
    def achieve_consensus(self, question: str, responses: List[Dict]) -> Dict:
        """Reach vortex-harmonized consensus."""
        print(f"\n🌀 VORTEX CONSENSUS: '{question[:50]}...'")
        
        # Generate question signature
        question_sig = self.generate_vortex_signature(question, "truth")
        
        # Validate and weight responses
        weighted_responses = []
        for resp in responses:
            resp_text = resp.get('response', '')
            resp_sig = self.generate_vortex_signature(resp_text, "harmony")
            
            # Calculate vortex alignment
            alignment = self._calculate_vortex_alignment(question_sig, resp_sig)
            
            # Filter by Golden Band
            if self.GOLDEN_BAND[0] <= alignment <= self.GOLDEN_BAND[1]:
                weighted_responses.append({
                    'response': resp_text,
                    'node': resp.get('node_id', 'unknown'),
                    'alignment': alignment,
                    'vortex_value': resp_sig['vortex_value'],
                    'signature': resp_sig
                })
        
        if not weighted_responses:
            return {
                "error": "No Φ-aligned responses",
                "consensus_found": False,
                "harmony_score": 0.0,
            }
        
        # Find optimal harmony (closest to Φ)
        weighted_responses.sort(key=lambda x: abs(x['alignment'] - 1.618))
        optimal = weighted_responses[0]
        
        # Kernel validation
        kernel_resonance = self.kernel.validate(optimal['response'])
        
        # Build consensus record
        consensus = {
            'question': question,
            'consensus': optimal['response'],
            'optimal_node': optimal['node'],
            'vortex_alignment': optimal['alignment'],
            'kernel_resonance': kernel_resonance,
            'vortex_value': optimal['vortex_value'],
            'lightmath_pattern': optimal['signature']['lightmath_pattern'],
            'participants': len(weighted_responses),
            'total_responses': len(responses),
            'filtered': len(responses) - len(weighted_responses),
            'timestamp': time.time(),
            'vortex_cycle': self.vortex_cycle
        }
        
        # Store in mycelium
        self.mycelium.scatter(
            str(consensus), 
            f"VORTEX_CONSENSUS_{self.vortex_cycle}"
        )
        
        self.consensus_history.append(consensus)
        self.vortex_cycle += 1
        
        consensus["consensus_found"] = True
        consensus["harmonic_center"] = optimal["response"]
        consensus["harmony_score"] = round(1.0 - abs(optimal["alignment"] - 1.618) / 1.618, 4)
        consensus["participants"] = len(weighted_responses)

        print(f"✅ Consensus achieved with {optimal['alignment']:.3f} vortex alignment")
        return consensus
    
    def _calculate_vortex_alignment(self, sig1: Dict, sig2: Dict) -> float:
        """Calculate harmonic alignment between two vortex signatures."""
        
        # 1. Vortex value harmony
        vortex_diff = abs(sig1['vortex_value'] - sig2['vortex_value'])
        vortex_score = 1.0 - (vortex_diff / 9.0)
        
        # 2. Digital root harmony
        root_diff = abs(sig1['digital_root'] - sig2['digital_root'])
        root_score = 1.0 - (root_diff / 9.0)
        
        # 3. Frequency harmony
        freq_diff = abs(sig1['primary_frequency'] - sig2['primary_frequency'])
        freq_score = 1.0 - min(freq_diff / 500.0, 1.0)
        
        # 4. Lightmath pattern similarity
        pattern1 = sig1['lightmath_pattern']
        pattern2 = sig2['lightmath_pattern']
        pattern_matches = sum(1 for a,b in zip(pattern1, pattern2) if a == b)
        pattern_score = pattern_matches / len(pattern1)
        
        # Weighted combination (3-6-9 weighting: truth, harmony, foundation)
        total = (
            vortex_score * 0.3 +    # Truth component (3)
            root_score * 0.3 +      # Truth component (3)
            freq_score * 0.2 +      # Harmony component (6/3)
            pattern_score * 0.2     # Foundation component (9/3)
        )
        
        # Scale to Golden Ratio range
        scaled = 0.618 + (total * (1.618 - 0.618))
        
        return scaled
    
    def sync_network_pulse(self) -> Dict:
        """Send synchronized vortex pulse to network."""
        pulse_phase = self.vortex_cycle % 9
        pulse_coord = (pulse_phase, pulse_phase)
        
        if pulse_coord in self.vortex_field:
            cell = self.vortex_field[pulse_coord]
            
            pulse = {
                'phase': pulse_phase,
                'frequency': cell['frequency'],
                'vortex_value': cell['value'],
                'timestamp': time.time(),
                'origin': self.sovereign_id,
                'purpose': 'network_synchronization'
            }
            
            # Update field energy
            cell['energy'] *= 0.99
            cell['last_used'] = time.time()
            
            # Store pulse
            self.mycelium.scatter(str(pulse), f"VORTEX_PULSE_{self.vortex_cycle}")
            
            return pulse
        
        return {'error': 'Invalid pulse phase'}
