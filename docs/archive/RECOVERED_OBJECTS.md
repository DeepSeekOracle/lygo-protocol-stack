# Recovered dangling objects (archived, not lost)

`git fsck` reported objects that are reachable from no branch — leftovers from dropped stashes,
force-updated deploy branches and abandoned work. Instead of letting `git gc` prune them, each
dangling commit was pinned to a local ref under `refs/archive/`, so the content is safe and
recoverable forever.

Recover a tree/file from one of them:

```bash
git log refs/archive/<name> -1
git show refs/archive/<name>:<path>
git checkout refs/archive/<name> -- <path>
```

These refs are local only (not pushed). List them with:

```bash
git for-each-ref --format='%(refname) %(objectname:short) %(subject)' refs/archive/
```

| commit | date | subject |
|---|---|---|
| `bd049bf` | 2026-07-04 | Biophase7: integrate pxpipe-LYGO module into lattice (P0 gate, proxy, manifests) |
| `678dfa7` | 2026-07-02 | security(joy-loop): SkillSpector hardening v2.3.1 — contracts, scoped caps, plant gate |
| `949928e` | 2026-09-17 | On main: wip-coli |
| `1230fab` | 2026-09-19 | On main: autostash |
| `74b608f` | 2026-07-04 | deploy: f6fb5039976558c4accc74c36c27f1bba328bb6c |
| `11505bb` | 2026-07-02 | deploy: a9d95f21f2d17a7eacf6e84e932407f5f2f2beee |
| `6d50cdc` | 2026-09-17 | On main: wip |
| `7d6a475` | 2026-09-17 | On main: wip |
| `8fea9e5` | 2026-09-17 | On main: wip-before-seed-push |
| `e2ecf5f` | 2026-09-16 | On main: wip-unrelated-before-1.2.0-push |
| `0ded73c` | 2026-07-08 | deploy: 25062193ea136891c083a82cca4907e5ec30d349 |
| `a36d115` | 2026-07-04 | deploy: e87955642e17662bdfd54244be68a2e628f36853 |
| `f06eca7` | 2026-07-02 | deploy: 48504498539628712a00c32608455fda8cb0798c |
| `2270d9b` | 2026-07-02 | deploy: ac1469328c0bc35414cc92677ddf6828184eab97 |
| `b0f9160` | 2026-07-03 | Lattice ground zero: file-integrity-checker ClawHub, operator 1.0.7, honest P0 skills, LATTICE_GROUND_ZERO |
| `967aa7b` | 2026-07-08 | deploy: 6efe08df7baa0417c781de7ae6615c8e234f8924 |

Dangling blobs (2339) and trees (10) were left to the normal gc grace period; they need no refs.
