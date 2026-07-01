# Human-gated publish checklist (Phase 3)

**Do not automate without operator present.**

## ClawHub

```bash
cd lygo-protocol-stack/clawhub/mirrors/lygo-docker-deploy
npx clawhub@latest publish . --slug lygo-docker-deploy --name "LYGO Docker Deploy"

cd ../lygo-alignment-badge
npx clawhub@latest publish . --slug lygo-alignment-badge --name "LYGO Alignment Badge"

cd ../lygo-protocol-stack-operator
npx clawhub@latest publish . --slug lygo-protocol-stack-operator --name "LYGO Protocol Stack Operator"
```

## Hugging Face dataset

```bash
cd lygo-protocol-stack
python tools/hf_push_dataset.py
python tools/bundle_hf_space_stack.py --mode=twin-gate
python tools/hf_push_space.py --message "Phase 3 twin harmonization + mesh gossip"
```

## GitHub main

```bash
git push origin main
```

## Grokipedia

Upload content from `docs/GROkipedia_PHASE3.md` + `docs/PHASE2_DEPLOYMENT.md` via Grokipedia editor.