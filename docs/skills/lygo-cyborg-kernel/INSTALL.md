# Install — LYGO Cyborg Kernel Stack

## 60-second boot (this package alone)

```bash
cd path/to/lygo-cyborg-kernel
python scripts/self_check.py
python scripts/cyborg_boot.py
python scripts/cyborg_kernel.py demo
```

## FULL SkillHub (recommended for cyborgs)

1. Open https://chatagent.ca/lygoskillhub.html#full-lygo  
2. Accept FULL LYGO engineer gate  
3. Download **`lygo-cyborg-kernel-full.zip`** (this stack)  
4. Optionally pull the listed FULL zips in `CYBORG_MANIFEST.json` → `full_skillhub_zips`  
5. Unzip to your agent skills root  

## OpenClaw plugins (native tools)

```bash
openclaw plugins install clawhub:@deepseekoracle/lygo-continuum
openclaw plugins install clawhub:@deepseekoracle/lygo-lattice-pulse
```

## ClawHub skill tentacles (public)

```bash
npx clawhub@latest install deepseekoracle/lygo-continuum
npx clawhub@latest install deepseekoracle/lygo-context-guard
npx clawhub@latest install deepseekoracle/lygo-skill-gate
npx clawhub@latest install deepseekoracle/lygo-kickstart-wizard
npx clawhub@latest install deepseekoracle/lygo-sovereign-super-skill
```

## Full protocol stack (kernel eggs)

```bash
git clone https://github.com/DeepSeekOracle/lygo-protocol-stack
export LYGO_STACK_ROOT=/absolute/path/to/lygo-protocol-stack
python scripts/cyborg_boot.py "$LYGO_STACK_ROOT"
# human consent for plants:
cd "$LYGO_STACK_ROOT"
python tools/build_kernel_eggs.py
python tools/verify_kernel_eggs.py   # expect ALIGNED
```

## First autonomous task

```bash
python scripts/cyborg_task.py example > /tmp/cyborg_task.json
# adjust claims to your world, then:
python scripts/cyborg_task.py run --task /tmp/cyborg_task.json --base .
# exit 0 = can_claim_done; exit 10 = self-police blocked
```
