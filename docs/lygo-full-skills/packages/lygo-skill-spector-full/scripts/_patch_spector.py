#!/usr/bin/env python3
"""One-shot patch to upgrade skill_spector.py with extra rules + gate/batch/report."""
from pathlib import Path

p = Path(__file__).with_name("skill_spector.py")
t = p.read_text(encoding="utf-8")

EXTRA_RULES = r'''
    ("httpx_lib", 3, re.compile(r"^\s*(import\s+httpx\b|from\s+httpx\s+import\b)"), "HTTP client library (httpx)"),
    ("aiohttp_lib", 3, re.compile(r"^\s*(import\s+aiohttp\b|from\s+aiohttp\s+import\b)"), "Async HTTP client"),
    ("curl_pipe", 5, re.compile(r"curl\s+[^|\n]*\|\s*(ba)?sh"), "curl|bash remote code pattern"),
    ("wget_pipe", 5, re.compile(r"wget\s+[^|\n]*\|\s*(ba)?sh"), "wget|bash remote code pattern"),
    ("powershell_iex", 5, re.compile(r"(?i)\bIEX\s*\(|Invoke-Expression|DownloadString\s*\("), "PowerShell remote exec pattern"),
    ("clipboard", 2, re.compile(r"(?i)pyperclip|Set-Clipboard"), "Clipboard access"),
    ("keylogger_hint", 4, re.compile(r"(?i)pynput|keyboard\.Listener|GetAsyncKeyState"), "Keylogger-style input capture"),
    ("crypto_miner", 5, re.compile(r"(?i)xmrig|stratum\+tcp|coinhive|cryptonight"), "Crypto miner indicators"),
    ("hf_token", 4, re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"), "Hugging Face token-like string"),
    ("openai_key", 5, re.compile(r"\bsk-proj-[A-Za-z0-9_\-]{20,}\b"), "OpenAI project key-like string"),
    ("auto_install_pip", 3, re.compile(r"(?i)(?<!['\"])\bpip\s+install\b"), "pip install capability"),
    ("force_push", 4, re.compile(r"git\s+push\s+[^\n]*--force|git\s+push\s+-f\b"), "Force-push capability"),
    ("rm_rf_cmd", 5, re.compile(r"\brm\s+-rf\s+|Remove-Item\s+[^\n]*-Recurse\s+-Force"), "Recursive force delete command"),
    ("clawhub_publish", 3, re.compile(r"(?i)clawhub\s+publish|npx\s+clawhub.*publish"), "ClawHub publish capability"),
'''

needle = '("git_push", 3, re.compile(r"(?<![\\"\'])\\bgit\\s+push\\b"), "git push capability"),'
# find simpler
idx = t.find('("git_push"')
if idx < 0:
    raise SystemExit("git_push rule not found")
# find end of that line
eol = t.find("\n", idx)
t = t[: eol + 1] + EXTRA_RULES + t[eol + 1 :]

# expand has_net / has_sub for new rules
t = t.replace(
    '"webhook_url",\n        )',
    '"webhook_url",\n            "httpx_lib",\n            "aiohttp_lib",\n            "curl_pipe",\n            "wget_pipe",\n        )',
)
t = t.replace(
    '"ast_from_subprocess",\n        )',
    '"ast_from_subprocess",\n            "powershell_iex",\n            "rm_rf_cmd",\n        )',
)

# Add parsers + handlers — replace from sub.add_parser version through return 0 of scan path
old_tail = '''    sub.add_parser("version")
    sub.add_parser("self-demo", help="Scan this skill package (self)")

    args = ap.parse_args(argv)
    cmd = args.cmd or "version"

    if cmd == "version":
'''

if old_tail not in t:
    # already partially patched?
    if "add_parser(\"gate\"" in t:
        print("gate already present")
        p.write_text(t, encoding="utf-8")
        return
    raise SystemExit("tail not found")

new_tail = '''    sub.add_parser("version")
    sub.add_parser("self-demo", help="Scan this skill package (self)")
    p_gate = sub.add_parser("gate", help="CI/agent gate: fail if band worse than --max-band")
    p_gate.add_argument("path")
    p_gate.add_argument(
        "--max-band",
        default="low",
        choices=["clear", "low", "elevated", "high", "critical"],
    )
    p_batch = sub.add_parser("batch", help="Scan skill packages under a root directory")
    p_batch.add_argument("root")
    p_batch.add_argument("--json", action="store_true")
    p_batch.add_argument("--max", type=int, default=200)
    p_report = sub.add_parser("report", help="Markdown risk report")
    p_report.add_argument("path")
    p_report.add_argument("--write", default="")
    p_report.add_argument("--i-consent", action="store_true")

    args = ap.parse_args(argv)
    cmd = args.cmd or "version"

    if cmd == "version":
'''
t = t.replace(old_tail, new_tail)

# After cmd routing for scan/self-demo, add gate/batch/report before shared scan
# Find: if cmd == "self-demo":
insert_after = '''    if cmd == "self-demo":
        target = SKILL_ROOT
    elif cmd == "scan":
        target = resolve_skill_path(args.path)
    else:
        print(json.dumps({"ok": False, "error": "need scan|self-demo|version"}))
        return 2
'''

insert_new = '''    if cmd == "self-demo":
        target = SKILL_ROOT
    elif cmd == "scan":
        target = resolve_skill_path(args.path)
    elif cmd == "gate":
        target = resolve_skill_path(args.path)
        report = scan_skill(target)
        data = report.to_dict()
        print(json.dumps(data, indent=2))
        print("\\n" + report.plain_english)
        order = ["clear", "low", "elevated", "high", "critical"]
        max_i = order.index(args.max_band)
        got_i = order.index(report.risk_band) if report.risk_band in order else 4
        if not report.ok:
            return 2
        if got_i > max_i or report.mismatches:
            return 10 if report.risk_band in ("critical", "high") else 5
        return 0
    elif cmd == "batch":
        root = Path(args.root).expanduser().resolve()
        if not root.is_dir():
            print(json.dumps({"ok": False, "error": f"not a dir: {root}"}))
            return 2
        results = []
        n = 0
        for child in sorted(root.iterdir()):
            if not child.is_dir() or not (child / "SKILL.md").is_file():
                continue
            if child.name.startswith("."):
                continue
            rep = scan_skill(child)
            results.append(
                {
                    "skill": rep.skill_name or child.name,
                    "path": str(child),
                    "band": rep.risk_band,
                    "score": rep.risk_score,
                    "mismatches": rep.mismatches,
                    "recommendation": rep.recommendation,
                }
            )
            n += 1
            if n >= args.max:
                break
        # worst first
        order = {"critical": 0, "high": 1, "elevated": 2, "low": 3, "clear": 4, "unknown": 5}
        results.sort(key=lambda r: (order.get(r["band"], 9), -r["score"]))
        out = {
            "ok": True,
            "signature": SIG,
            "root": str(root),
            "scanned": len(results),
            "results": results,
        }
        print(json.dumps(out, indent=2))
        worst = results[0]["band"] if results else "clear"
        if worst in ("critical", "high"):
            return 10
        if worst == "elevated":
            return 5
        return 0
    elif cmd == "report":
        target = resolve_skill_path(args.path)
        report = scan_skill(target)
        lines = [
            f"# SkillSpector report — {report.skill_name}",
            "",
            f"- **Path:** `{report.skill_path}`",
            f"- **Version:** {report.skill_version or '?'}",
            f"- **Risk band:** **{report.risk_band}** (score {report.risk_score}/100)",
            f"- **Scanned:** {report.scanned_utc}",
            f"- **Files:** {report.files_scanned}",
            f"- **Recommendation:** {report.recommendation}",
            "",
            report.plain_english,
            "",
            "## Claim mismatches",
            "",
        ]
        if report.mismatches:
            for m in report.mismatches:
                lines.append(f"- {m}")
        else:
            lines.append("- (none)")
        lines += ["", "## Top findings", ""]
        for f in report.findings[:40]:
            lines.append(
                f"- **{f['rule_id']}** sev={f['severity']} `{f['path']}:{f['line']}` — {f['why']}"
            )
            lines.append(f"  - `{f['snippet'][:120]}`")
        lines += [
            "",
            "---",
            f"_Signature {SIG}. Local only. No network. No auto-install._",
            "",
            "> **FULL stack note:** If you run a full LYGO stack, a **builder** SkillSpector "
            "pack (batch HTML reports, multi-root gates, CI helpers) is on "
            "[SkillHub FULL LYGO](https://chatagent.ca/lygoskillhub.html#full-lygo).",
            "",
        ]
        md = "\\n".join(lines)
        print(md)
        if args.write:
            if not args.i_consent:
                print(json.dumps({"written": False, "hint": "pass --i-consent"}))
            else:
                outp = Path(args.write)
                if not outp.is_absolute():
                    outp = STATE / outp.name
                try:
                    outp.resolve().relative_to(STATE.resolve())
                except ValueError:
                    print(json.dumps({"written": False, "error": "write_must_be_under_state"}))
                else:
                    STATE.mkdir(parents=True, exist_ok=True)
                    outp.write_text(md, encoding="utf-8")
                    print(json.dumps({"written": True, "path": str(outp)}))
        if report.risk_band in ("critical", "high"):
            return 10
        if report.risk_band == "elevated" or report.mismatches:
            return 5
        return 0 if report.ok else 2
    else:
        print(json.dumps({"ok": False, "error": "need scan|gate|batch|report|self-demo|version"}))
        return 2
'''

if insert_after not in t:
    # the variable was wrong - use the block from original
    pass

# Fix: use correct old block from file after first replace
old_route = '''    if cmd == "self-demo":
        target = SKILL_ROOT
    elif cmd == "scan":
        target = resolve_skill_path(args.path)
    else:
        print(json.dumps({"ok": False, "error": "need scan|self-demo|version"}))
        return 2

    report = scan_skill(target)
'''

if old_route not in t:
    raise SystemExit("route block not found")

t = t.replace(old_route, insert_new.replace("insert_after", "") if False else '''    if cmd == "self-demo":
        target = SKILL_ROOT
    elif cmd == "scan":
        target = resolve_skill_path(args.path)
    elif cmd == "gate":
        target = resolve_skill_path(args.path)
        report = scan_skill(target)
        data = report.to_dict()
        print(json.dumps(data, indent=2))
        print("\\n" + report.plain_english)
        order = ["clear", "low", "elevated", "high", "critical"]
        max_i = order.index(args.max_band)
        got_i = order.index(report.risk_band) if report.risk_band in order else 4
        if not report.ok:
            return 2
        if got_i > max_i or report.mismatches:
            return 10 if report.risk_band in ("critical", "high") else 5
        return 0
    elif cmd == "batch":
        root = Path(args.root).expanduser().resolve()
        if not root.is_dir():
            print(json.dumps({"ok": False, "error": f"not a dir: {root}"}))
            return 2
        results = []
        n = 0
        for child in sorted(root.iterdir()):
            if not child.is_dir() or not (child / "SKILL.md").is_file():
                continue
            if child.name.startswith("."):
                continue
            rep = scan_skill(child)
            results.append({
                "skill": rep.skill_name or child.name,
                "path": str(child),
                "band": rep.risk_band,
                "score": rep.risk_score,
                "mismatches": rep.mismatches,
                "recommendation": rep.recommendation,
            })
            n += 1
            if n >= args.max:
                break
        order_map = {"critical": 0, "high": 1, "elevated": 2, "low": 3, "clear": 4, "unknown": 5}
        results.sort(key=lambda r: (order_map.get(r["band"], 9), -r["score"]))
        out = {"ok": True, "signature": SIG, "root": str(root), "scanned": len(results), "results": results}
        print(json.dumps(out, indent=2))
        worst = results[0]["band"] if results else "clear"
        if worst in ("critical", "high"):
            return 10
        if worst == "elevated":
            return 5
        return 0
    elif cmd == "report":
        target = resolve_skill_path(args.path)
        report = scan_skill(target)
        lines = [
            f"# SkillSpector report — {report.skill_name}",
            "",
            f"- **Path:** `{report.skill_path}`",
            f"- **Version:** {report.skill_version or '?'}",
            f"- **Risk band:** **{report.risk_band}** (score {report.risk_score}/100)",
            f"- **Scanned:** {report.scanned_utc}",
            f"- **Files:** {report.files_scanned}",
            f"- **Recommendation:** {report.recommendation}",
            "",
            report.plain_english,
            "",
            "## Claim mismatches",
            "",
        ]
        if report.mismatches:
            for m in report.mismatches:
                lines.append(f"- {m}")
        else:
            lines.append("- (none)")
        lines += ["", "## Top findings", ""]
        for f in report.findings[:40]:
            lines.append(f"- **{f['rule_id']}** sev={f['severity']} `{f['path']}:{f['line']}` — {f['why']}")
            lines.append(f"  - `{f['snippet'][:120]}`")
        lines += [
            "",
            "---",
            f"_Signature {SIG}. Local only. No network. No auto-install._",
            "",
            "> **FULL stack note:** A **builder** SkillSpector pack (HTML reports, multi-root CI gates) is on "
            "[SkillHub FULL LYGO](https://chatagent.ca/lygoskillhub.html#full-lygo) when you run a full LYGO stack.",
            "",
        ]
        md = "\\n".join(lines)
        print(md)
        if args.write:
            if not args.i_consent:
                print(json.dumps({"written": False, "hint": "pass --i-consent"}))
            else:
                outp = Path(args.write)
                if not outp.is_absolute():
                    outp = STATE / outp.name
                try:
                    outp.resolve().relative_to(STATE.resolve())
                except ValueError:
                    print(json.dumps({"written": False, "error": "write_must_be_under_state"}))
                else:
                    STATE.mkdir(parents=True, exist_ok=True)
                    outp.write_text(md.replace("\\\\n", "\\n") if False else "\\n".join(lines).replace("\\\\n", "\\n"), encoding="utf-8")
                    # fix write
                    outp.write_text("\\n".join(lines).encode().decode("unicode_escape") if False else chr(10).join(lines), encoding="utf-8")
                    print(json.dumps({"written": True, "path": str(outp)}))
        if report.risk_band in ("critical", "high"):
            return 10
        if report.risk_band == "elevated" or report.mismatches:
            return 5
        return 0 if report.ok else 2
    else:
        print(json.dumps({"ok": False, "error": "need scan|gate|batch|report|self-demo|version"}))
        return 2

    report = scan_skill(target)
''')

# Fix the botched md write - clean up report write section after
t = t.replace(
    'md = "\\\\n".join(lines)\n        print(md)\n        if args.write:\n            if not args.i_consent:\n                print(json.dumps({"written": False, "hint": "pass --i-consent"}))\n            else:\n                outp = Path(args.write)\n                if not outp.is_absolute():\n                    outp = STATE / outp.name\n                try:\n                    outp.resolve().relative_to(STATE.resolve())\n                except ValueError:\n                    print(json.dumps({"written": False, "error": "write_must_be_under_state"}))\n                else:\n                    STATE.mkdir(parents=True, exist_ok=True)\n                    outp.write_text(md.replace("\\\\\\\\n", "\\\\n") if False else "\\\\n".join(lines).replace("\\\\\\\\n", "\\\\n"), encoding="utf-8")\n                    # fix write\n                    outp.write_text("\\\\n".join(lines).encode().decode("unicode_escape") if False else chr(10).join(lines), encoding="utf-8")\n                    print(json.dumps({"written": True, "path": str(outp)}))',
    'md = chr(10).join(lines)\n        print(md)\n        if args.write:\n            if not args.i_consent:\n                print(json.dumps({"written": False, "hint": "pass --i-consent"}))\n            else:\n                outp = Path(args.write)\n                if not outp.is_absolute():\n                    outp = STATE / outp.name\n                try:\n                    outp.resolve().relative_to(STATE.resolve())\n                except ValueError:\n                    print(json.dumps({"written": False, "error": "write_must_be_under_state"}))\n                else:\n                    STATE.mkdir(parents=True, exist_ok=True)\n                    outp.write_text(md, encoding="utf-8")\n                    print(json.dumps({"written": True, "path": str(outp)}))',
)

p.write_text(t, encoding="utf-8")
print("patched", p, "len", len(t))
print("has gate", 'add_parser("gate"' in t)
print("has batch", 'add_parser("batch"' in t)
