#!/usr/bin/env python3
"""Read-only integrity audit for Haven Star Chart registry. Does not modify data."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
issues: list[str] = []
warns: list[str] = []
oks: list[str] = []


def issue(msg: str) -> None:
    issues.append(msg)


def warn(msg: str) -> None:
    warns.append(msg)


def good(msg: str) -> None:
    oks.append(msg)


def main() -> int:
    p1 = ROOT / "docs" / "haven_star_chart_data.json"
    p2 = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_data.json"
    b1 = p1.read_bytes()
    b2 = p2.read_bytes()
    if b1 == b2:
        good("alias files identical (root + haven_star_chart/)")
    else:
        issue(
            f"alias mismatch sizes {len(b1)} vs {len(b2)} "
            f"sha {hashlib.sha256(b1).hexdigest()[:12]} vs {hashlib.sha256(b2).hexdigest()[:12]}"
        )

    d = json.loads(b1.decode("utf-8"))
    nodes = d.get("nodes") or []
    links = d.get("links") or []
    portals = d.get("portals") or []
    cosmos = d.get("cosmos") or {}

    if d.get("node_count") != len(nodes):
        issue(f"node_count field {d.get('node_count')} != len(nodes) {len(nodes)}")
    else:
        good(f"node_count consistent: {len(nodes)}")

    if d.get("link_count") != len(links):
        issue(f"link_count field {d.get('link_count')} != len(links) {len(links)}")
    else:
        good(f"link_count consistent: {len(links)}")

    kinds = Counter(n.get("kind") for n in nodes)
    lattice_n = kinds.get("lattice", 0)
    if d.get("lattice_count") != lattice_n:
        issue(f"lattice_count field {d.get('lattice_count')} != actual lattice {lattice_n}")
    else:
        good(f"lattice_count consistent: {lattice_n}")

    champ_n = kinds.get("champion", 0)
    if d.get("champion_count") != champ_n:
        issue(f"champion_count field {d.get('champion_count')} != actual {champ_n}")
    else:
        good(f"champion_count consistent: {champ_n}")

    seal_n = kinds.get("seal", 0)
    if d.get("seal_count") != seal_n:
        warn(f"seal_count field {d.get('seal_count')} vs kind=seal {seal_n}")
    else:
        good(f"seal_count consistent: {seal_n}")

    print("kinds:", dict(kinds.most_common()))

    ids = [n.get("id") for n in nodes]
    if any(not i for i in ids):
        issue(f"nodes with empty id: {sum(1 for i in ids if not i)}")
    id_counts = Counter(ids)
    dups = [i for i, c in id_counts.items() if c > 1 and i]
    if dups:
        issue(f"duplicate node ids ({len(dups)}): {dups[:15]}")
    else:
        good(f"unique node ids: {len(id_counts)}")

    id_set = set(ids)
    for need in (
        "SEAL_000",
        "CHAMPION_LIGHTFATHER",
        "PORTAL_STACK",
        "PORTAL_CLAWHUB",
        "LATTICE_CLAWHUB_PUBLISHER",
    ):
        if need in id_set:
            good(f"core present: {need}")
        else:
            issue(f"missing core node: {need}")

    champs = [n for n in nodes if n.get("kind") == "champion"]
    if len(champs) < 15:
        warn(f"champion kind nodes: {len(champs)} (expect >=15 council)")
    else:
        good(f"champions: {len(champs)}")

    skills = [n for n in nodes if str(n.get("id", "")).startswith("LATTICE_SKILL_")]
    if len(skills) < 60:
        issue(f"only {len(skills)} LATTICE_SKILL_* nodes")
    else:
        good(f"LATTICE_SKILL_* count: {len(skills)}")

    bad_skill = sum(1 for n in skills if not n.get("name"))
    no_url = sum(1 for n in skills if not (n.get("urls") or {}).get("clawhub"))
    bad_cosmos = sum(
        1 for n in skills if (n.get("cosmos") or {}).get("nebula_id") != "NEBULA_CLAWHUB_SKILLS"
    )
    if bad_skill:
        issue(f"skills missing name: {bad_skill}")
    else:
        good("all skills have names")
    if no_url:
        issue(f"skills missing clawhub url: {no_url}")
    else:
        good("all skills have clawhub urls")
    if bad_cosmos:
        warn(f"skills not in NEBULA_CLAWHUB_SKILLS: {bad_cosmos}")
    else:
        good("all skills in NEBULA_CLAWHUB_SKILLS nebula")

    skill_gals = Counter((n.get("cosmos") or {}).get("galaxy_id") for n in skills)
    print("skill galaxies:", dict(skill_gals))

    missing_fields = 0
    for n in nodes:
        if not n.get("id") or not n.get("kind") or not n.get("name"):
            missing_fields += 1
    if missing_fields:
        issue(f"nodes missing id/kind/name: {missing_fields}")
    else:
        good("all nodes have id/kind/name")

    # connections
    portal_ids = {p.get("id") for p in portals if p.get("id")}
    dangling_conn = 0
    conn_samples: list[tuple] = []
    for n in nodes:
        for c in n.get("connections") or []:
            if c not in id_set and c not in portal_ids:
                dangling_conn += 1
                if len(conn_samples) < 12:
                    conn_samples.append((n.get("id"), c))
    if dangling_conn:
        warn(f"dangling connection refs: {dangling_conn} e.g. {conn_samples[:8]}")
    else:
        good("all connection refs resolve to nodes/portals")

    # links — detect shape
    if links:
        print("link sample keys:", list(links[0].keys()))
        print("link sample:", {k: links[0].get(k) for k in list(links[0].keys())[:8]})

    def ends(L: dict) -> tuple:
        a = L.get("source") or L.get("from") or L.get("a") or L.get("source_id")
        b = L.get("target") or L.get("to") or L.get("b") or L.get("target_id")
        if a is None and "nodes" in L and isinstance(L["nodes"], list) and len(L["nodes"]) >= 2:
            a, b = L["nodes"][0], L["nodes"][1]
        return a, b

    bad_links = 0
    link_samples: list = []
    self_loops = 0
    for L in links:
        a, b = ends(L)
        if a and a not in id_set:
            bad_links += 1
            if len(link_samples) < 8:
                link_samples.append(("src", a))
        if b and b not in id_set:
            bad_links += 1
            if len(link_samples) < 8:
                link_samples.append(("tgt", b))
        if a and a == b:
            self_loops += 1
    if bad_links:
        issue(f"links with unknown endpoints: {bad_links} e.g. {link_samples[:5]}")
    else:
        good(f"all {len(links)} links have known endpoints")
    if self_loops:
        warn(f"self-loop links: {self_loops}")
    else:
        good("no self-loop links")

    for key in ("galaxies", "nebulae", "clusters"):
        if key not in cosmos:
            issue(f"cosmos missing {key}")
        else:
            good(f"cosmos has {key}: {len(cosmos[key])}")

    no_cosmos_nonportal = [
        n.get("id")
        for n in nodes
        if not n.get("cosmos")
        and n.get("id") not in portal_ids
        and n.get("kind") not in ("portal",)
    ]
    if no_cosmos_nonportal:
        warn(
            f"non-portal nodes without cosmos: {len(no_cosmos_nonportal)} e.g. {no_cosmos_nonportal[:8]}"
        )
    else:
        good("non-portal nodes have cosmos placement")

    # registry hash
    blob = json.dumps(nodes, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    if digest != d.get("registry_sha256"):
        issue(
            f"registry_sha256 mismatch recompute {digest[:16]} vs stored {(d.get('registry_sha256') or '')[:16]}"
        )
    else:
        good("registry_sha256 matches recomputed node digest")

    meta_path = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_meta.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("registry_sha256") != d.get("registry_sha256"):
            issue("meta.registry_sha256 != data.registry_sha256")
        else:
            good("meta matches data registry_sha256")
        if meta.get("node_count") != d.get("node_count"):
            issue(f"meta.node_count {meta.get('node_count')} != data {d.get('node_count')}")
        else:
            good("meta.node_count matches")

    mp = ROOT / "docs" / "clawhub_star_chart_map.json"
    if mp.is_file():
        m = json.loads(mp.read_text(encoding="utf-8"))
        if m.get("skill_nodes") != len(skills):
            warn(f"map report skill_nodes {m.get('skill_nodes')} vs chart {len(skills)}")
        else:
            good(f"map report skill_nodes matches ({len(skills)})")
        map_slugs = set(m.get("slugs") or [])
        chart_slugs = {
            (n.get("meta") or {}).get("slug") or n["id"].replace("LATTICE_SKILL_", "")
            for n in skills
        }
        if map_slugs != chart_slugs:
            warn(
                f"map vs chart slug mismatch only_map={sorted(map_slugs-chart_slugs)[:8]} "
                f"only_chart={sorted(chart_slugs-map_slugs)[:8]}"
            )
        else:
            good("map report slug set == chart skill slugs")

    feed_p = ROOT / "docs" / "haven_star_chart" / "haven_star_chart_feed.json"
    if feed_p.is_file():
        feed = json.loads(feed_p.read_text(encoding="utf-8"))
        entries = feed.get("entries") or feed.get("feed") or []
        ec = feed.get("entry_count")
        if ec is None:
            ec = len(entries) if isinstance(entries, list) else "?"
        good(f"feed present entry_count={ec} chain_valid={feed.get('chain_valid')}")
        if feed.get("chain_valid") is False:
            issue("feed chain_valid is false")

    mb = len(b1) / (1024 * 1024)
    if mb > 8:
        warn(f"data JSON large: {mb:.2f} MB — may slow mobile browsers")
    else:
        good(f"data JSON size OK: {mb:.2f} MB")

    html = (ROOT / "docs" / "HavenStarChart.html").read_text(encoding="utf-8", errors="replace")
    if "haven_star_chart/haven_star_chart_data.json" in html:
        good("HTML references haven_star_chart/haven_star_chart_data.json")
    else:
        issue("HTML missing expected data path string")

    # music / seals not regressed
    music = sum(1 for n in nodes if n.get("kind") == "music_track")
    if music < 500:
        warn(f"music_track count low: {music}")
    else:
        good(f"music_track nodes intact: {music}")

    # dangerous empty tags/urls on skill hub
    hub = next((n for n in nodes if n.get("id") == "LATTICE_CLAWHUB_PUBLISHER"), None)
    if hub:
        good(f"publisher hub name: {hub.get('name')}")
        if "CLAWHUB" not in (hub.get("tags") or []):
            warn("publisher hub missing CLAWHUB tag")

    print("\n========== AUDIT SUMMARY ==========")
    print(f"OK: {len(oks)}  WARN: {len(warns)}  ISSUE: {len(issues)}")
    print("--- ISSUES ---")
    for m in issues:
        print(" ISSUE:", m)
    print("--- WARNS ---")
    for m in warns:
        print(" WARN:", m)
    print("--- OK ---")
    for m in oks:
        print(" OK:", m)
    print("RESULT:", "PASS" if not issues else "FAIL")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
