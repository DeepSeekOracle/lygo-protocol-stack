#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess
import tempfile

html = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html").read_text(encoding="utf-8")
print("html len", len(html))

scripts = []
for m in re.finditer(r"<script(?![^>]*application/json)([^>]*)>([\s\S]*?)</script>", html):
    scripts.append(m.group(2))
print("script count", len(scripts), "sizes", [len(s) for s in scripts])
main = max(scripts, key=len) if scripts else ""
print("main len", len(main))
print("const audio", main.find("const audio"))
print("playbackSafety", main.find("playbackSafety"))
print("braces", main.count("{"), main.count("}"))
print("parens", main.count("("), main.count(")"))

# Show around const audio
i = main.find("const audio")
print("--- around audio ---")
print(main[max(0, i - 200) : i + 400])

tmp = Path(r"I:\E Drive\lygo-protocol-stack\_tmp_listen_main.js")
tmp.write_text(main, encoding="utf-8")
r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
print("node exit", r.returncode)
print(r.stdout)
print(r.stderr[:2000] if r.stderr else "")

# Find line number of error if any
if r.returncode != 0 and ":" in (r.stderr or ""):
    # node format: ...js:LINE
    m = re.search(r":(\d+)\n", r.stderr or "")
    if m:
        line = int(m.group(1))
        lines = main.splitlines()
        start = max(0, line - 5)
        end = min(len(lines), line + 5)
        print("--- error context ---")
        for n in range(start, end):
            mark = ">>" if n + 1 == line else "  "
            print(f"{mark}{n+1}: {lines[n][:200]}")
