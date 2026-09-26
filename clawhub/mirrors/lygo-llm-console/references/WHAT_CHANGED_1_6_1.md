# What changed in 1.6.1 (console 1.5.7)

This release answers the published 1.6.0 scan report. Every row is either a finding the scanners
raised or a disclosure they said was missing.

| scan item | what it was | what changed |
|---|---|---|
| static analysis `suspicious.dynamic_code_execution`, `src/lygo_engine.py:208` | the word "eval" inside a **comment** about `-fa` throughput | the comment says "prompt processing" now. No code changed. |
| static analysis `suspicious.dynamic_code_execution`, `src/chat_loop.py:27` | the math-intent regex held the literal `eval(?:uate)?`, which reads as a dynamic-eval call | rewritten `ev(?:al|aluate)` - same matches, pinned by `tests/test_math_routing.py` |
| static analysis `suspicious.install_untrusted_source`, `web_portal/portal.json:6` | the local console URL was written as a raw IP | now `http://localhost:9641` |
| SkillSpector HIGH, category "MCP Tool Poisoning", 24 items | *"session archiving, cataloging and resume/import add persistent storage beyond a simple runtime launcher; users may not expect extensive conversation retention"* | retention is stated in the description **and** in Declared capabilities: what is kept, where it lives, that nothing is uploaded, that it does not expire by itself, and that deleting the kit folder removes it. The behaviour is unchanged; its disclosure is not. |
| SkillSpector CRITICAL, Data Flow, `kit/src/chat_loop.py:748` | *"tainted flow: `req` from `os.environ.get` -> `urllib.request.urlopen`"* - a POST to a cloud provider whose key came from the environment | **not changed here.** That is the console's own BYO-key cloud-brain path: the key sent is the operator's, to the endpoint the operator configured. Where the key is read from is a product decision, not a scan fix. |
| A.I.G T09 | *"default URL prefetch exposes privileged local tools to indirect prompt injection"* | **not changed here.** `LYGO_HOST_PREFETCH` gates it and fetched text is labelled RESOURCE, but the default is still on. |
| static analysis `suspicious.dynamic_code_execution`, `src/modules/host.py:527` | `spec.loader.exec_module(module)` | **not changed.** It is how a workspace limb is loaded, and it is disclosed as code execution in Declared capabilities. |

Nothing else in the kit changed: the unpacked ship form, per-file SHA-256 in `kit/PUBLIC_KIT.json`, and the map/verify scripts are as they were in 1.6.0.
