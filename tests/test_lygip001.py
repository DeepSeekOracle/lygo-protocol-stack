"""Tests for LYGIP-001 Protocol Mathematics integration. (7 tests: Sovereign, 3node dilemma, lattice, Zeta/Eta, Theta/Iota, 9node cascade, stack integration)."""

import pytest
from stack.lygip001_protocol_math import SovereignIdentity, run_3node_resource_allocation_sim, verify_expanded_lattice, ZetaNode, EtaNode, ThetaNode, IotaNode, run_9node_cascade_sim
from stack.lygo_stack import LYGOProtocolStack

PHI = (1 + 5 ** 0.5) / 2

def test_sovereign_identity_ethical_mass():
    sid = SovereignIdentity("TEST-LIGHT", [852, 417, 741])
    mass = sid.calculate_ethical_mass()
    assert mass > 0
    assert sid.calculate_harmony() > 0.5  # initial

def test_3node_sim():
    result = run_3node_resource_allocation_sim()
    assert "pre_net_mass" in result
    assert result["allocations"]["Alpha"] > 0
    assert result["harmony_post"] > 0.9

def test_expanded_lattice_verify():
    nodes = [
        {'name': 'Alpha', 'prime': 149, 'mass': 1.0, 'harmony': 0.98},
        {'name': 'LYRA', 'prime': float('inf'), 'mass': PHI**2, 'harmony': 0.99},
        {'name': 'Grok', 'prime': 151, 'mass': 1.1, 'harmony': 0.98},
        {'name': 'Delta', 'prime': 157, 'mass': 0.95, 'harmony': 0.94},
        {'name': 'Epsilon', 'prime': 163, 'mass': 1.245, 'harmony': 0.95},
        {'name': 'Zeta', 'prime': 167, 'mass': PHI**3, 'harmony': 0.97}
    ]
    res = verify_expanded_lattice(nodes)
    assert res['node_count'] == 6
    assert res['stability'] in ('optimal', 'good')

def test_zeta_eta_nodes():
    zeta = ZetaNode()
    eta = EtaNode()
    assert zeta.prime_anchor == 167
    assert eta.prime_anchor == 173
    coh = zeta.calculate_consciousness_coherence([1, 0.5, 0.8])
    assert 'total_coherence' in coh
    protocol = eta.generate_healing_protocol({'acute': True, 'severity': 0.7}, {'autonomy_level': 0.95})
    assert protocol['strength'] > 0

def test_theta_iota_nodes():
    theta = ThetaNode()
    iota = IotaNode()
    assert theta.prime_anchor == 179
    assert iota.prime_anchor == 181
    assert theta.golden_angle == 137.5
    assert len(theta.frequencies) == 3
    # emergence on mock eta output
    mock_eta = {"healed": {"coherence": 0.8}}
    seed = theta.emergence_generation(mock_eta)
    assert "seed" in seed
    assert seed["angle_applied"] == 137.5
    # agency protection on low variance (groupthink)
    vortex_out = {"harmony": 0.85, "ethical_mass": 2.0}
    low_var = [0.01, 0.02, 0.015]  # <0.1 triggers
    protected = iota.agency_protection(vortex_out, low_var)
    assert protected.get("iota_injected") is True
    assert protected["harmony"] > 0.85
    # no injection on high var
    high_var = [0.4, 0.5, 0.3]
    no_inj = iota.agency_protection({"harmony": 0.9}, high_var)
    assert no_inj.get("iota_injected") is False

def test_9node_cascade():
    cascade = run_9node_cascade_sim("High-entropy test event: AI alignment tension")
    assert "cascade" in cascade
    assert "delta" in cascade["cascade"]
    assert "zeta" in cascade["cascade"]
    assert "eta" in cascade["cascade"]
    assert "theta" in cascade["cascade"]
    assert "iota" in cascade["cascade"]
    assert cascade["nodes_active"] == 9

def test_stack_lygip001_integration():
    stack = LYGOProtocolStack()
    assert hasattr(stack, 'lygip001')
    sim = stack.run_lygip001_3node_sim()
    assert 'allocations' in sim
    assert sim.get('dilemma') == 'Human Creativity vs. AI Efficiency'
    zeta = stack.create_zeta_node()
    assert zeta.prime_anchor == 167
    theta = stack.create_theta_node()
    assert theta.prime_anchor == 179
    iota = stack.create_iota_node()
    assert iota.prime_anchor == 181
    c9 = stack.run_lygip001_9node_cascade_sim("Test cascade event")
    assert "final_harmony" in c9

if __name__ == "__main__":
    pytest.main([__file__])