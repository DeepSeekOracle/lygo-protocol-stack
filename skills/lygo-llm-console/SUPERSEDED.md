# Superseded — this tree is the 1.2.0 package

**Do not publish from here.** The live ClawHub package is built from
[`clawhub/mirrors/lygo-llm-console`](../../../clawhub/mirrors/lygo-llm-console) and is at **1.6.0**
(console 1.5.6, shipped as an unpacked kit).

This directory is kept for history only. It still carries 1.2.0 metadata, points at the old
`kit/lygo-llm-console-public.zip`, and describes a console two minor versions behind — the exact
combination that produced the four HIGH "referenced artifact was not completely inspected / embedded
NUL bytes" findings on the old registry scan.

| | here (1.2.0) | live (1.6.0) |
|---|---|---|
| source | this tree | `clawhub/mirrors/lygo-llm-console` |
| kit | one zip | unpacked tree, per-file SHA-256 in `kit/PUBLIC_KIT.json` |
| audit | SkillSpector CRITICAL, 33 issues, 5 HIGH, DO_NOT_INSTALL | one finding (host prefetch) plus static notes for the code-execution limbs |

If you need the current package: <https://clawhub.ai/deepseekoracle/skills/lygo-llm-console>
Page: <https://chatagent.ca/lygo-llm-console.html>
