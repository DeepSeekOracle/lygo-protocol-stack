# LoRa mesh transport (Layer D-RF)

**Signature:** `Delta9Phi963-LYGO-LORA-MESH-v1.0.0`  
**Skill:** [lygo-lora-mesh](https://clawhub.ai/deepseekoracle/skills/lygo-lora-mesh)  
**Codec home:** `clawhub/mirrors/lygo-lora-mesh/scripts/lygo_lora.py`

When HTTPS is up, use living-mesh HTTP gossip. When it is not, send a **text** pulse on **stock Meshtastic**. Do not fork firmware.

```text
LY1/<node_id>/<64-hex roots_digest>/<A|F|Q|S>/<hop 0-7>
```

Cap: **200 bytes** (Meshtastic ~237). No eggs, agent cards, TV, or Star Chart on RF. Missing radio = **NAMED_SHADOW**.

```bash
export LYGO_STACK_ROOT="I:\E Drive\lygo-protocol-stack"
python tools/lygo_lora_pulse.py encode
python tools/lygo_lora_pulse.py probe
python tools/lygo_lora_pulse.py ingest --pulse-file received.txt --i-consent
```

Ingest writes `data/living_mesh/lora_last.json` only.

Hardware list: skill `references/HARDWARE.md`. NA **915 MHz**.
