from pathlib import Path
import re

for p in [
    Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html"),
    Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html"),
]:
    t = p.read_text(encoding="utf-8")
    t = re.sub(
        r"\s*<div class=\"mp-info\">[\s\S]*?id=\"mp-expand\"[\s\S]*?</div>\s*",
        "\n",
        t,
        count=1,
    )
    t = re.sub(r"\s*<div class=\"mp-art\"[\s\S]*?</div>\s*", "\n", t)
    # leftover buttons if any
    for bid in ("mp-prev", "mp-play", "mp-next", "mp-expand", "mp-title", "mp-sub"):
        if bid in t:
            print("still has", bid)
    p.write_text(t, encoding="utf-8")
    print(p.name, "len", len(t), "mp-play", "mp-play" in t)
