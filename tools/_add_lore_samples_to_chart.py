import json, hashlib
from pathlib import Path
STACK = Path(r"D:\lygo-protocol-stack")
DATA = STACK / "data" / "eternal_haven"
ACC = STACK / "data" / "haven_star_chart" / "submissions" / "accepted"
samples = json.loads((DATA / "samples_index.json").read_text(encoding="utf-8"))["samples"]
book_map = {
    1: "LORE_BOOK_I_MOONLIT_SLUMBER",
    2: "LORE_BOOK_II_SHATTERED_ACCORD",
    3: "LORE_BOOK_III_ASCENSION_WAR",
    4: "LORE_BOOK_IV_ETERNAL_DAWNS",
}
for s in samples:
    nid = "LORE_SAMPLE_" + s["id"].upper().replace("-", "_")
    conns = ["LORE_ETERNAL_HAVEN_HUB"]
    if s.get("book") in book_map:
        conns.append(book_map[s["book"]])
    else:
        conns.append("CHAMPION_LIGHTFATHER")
    node = {
        "id": nid,
        "kind": "lore",
        "name": s["title"],
        "equation": "Truth = \u2207\u00b7(Light \u00d7 Story) \u2297 \u03949 \u00b7 963Hz",
        "glyph": "\U0001f3a7",
        "tone": "963Hz",
        "tags": ["LORE", "HAVEN", "SAMPLE", "ETERNAL_HAVEN", "AUDIO"],
        "connections": conns,
        "layer": 2,
        "urls": {
            "listen": s["stream_url"],
            "hf": "https://huggingface.co/datasets/DeepSeekOracle/eternal-haven-lore",
            "codex": "https://deepseekoracle.github.io/Excavationpro/EternalHavenCodex.html",
        },
    }
    dig = hashlib.sha256(json.dumps(node, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    sub = {
        "signature": "\u03949\u03a6963-HAVEN-STAR-SUBMISSION-v1",
        "submitter_type": "aligned_agent",
        "node": node,
        "content_sha256": dig,
    }
    (ACC / f"{nid}.json").write_text(json.dumps(sub, indent=2) + "\n", encoding="utf-8")
    print("wrote", nid)
