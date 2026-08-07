#!/usr/bin/env python3
"""Inject FULL LYGO engineer gate + packages into LYGOSKILLHUB HTML pages."""
from __future__ import annotations

import json
import re
from pathlib import Path

CATALOG = Path(r"D:\lygo-protocol-stack\docs\lygo-full-skills\catalog.json")
PAGES = [
    (
        Path(r"D:\lygo-protocol-stack\docs\LYGOSKILLHUB.html"),
        "lygo-full-skills/dist/",
        "lygo-full-skills/catalog.json",
    ),
    (
        Path(r"D:\Excavationpro\LYGOSKILLHUB.html"),
        "data/lygo-full-skills/dist/",
        "data/lygo-full-skills/catalog.json",
    ),
    (
        Path(r"D:\chatagent\lygoskillhub.html"),
        "data/lygo-full-skills/dist/",
        "data/lygo-full-skills/catalog.json",
    ),
]

CSS = r"""
/* FULL LYGO engineer gate */
.full-lygo-gate {
  margin: 1.75rem 0 0;
  border-radius: 14px;
  border: 1px solid rgba(255, 80, 80, 0.35);
  background:
    radial-gradient(ellipse 70% 50% at 80% 0%, rgba(255, 80, 80, 0.08) 0%, transparent 55%),
    rgba(18, 10, 12, 0.95);
  padding: 1.25rem 1.15rem 1.35rem;
}
.full-lygo-gate h2 {
  margin: 0 0 0.4rem;
  font-size: 1.05rem;
  color: #ff8a8a;
  letter-spacing: 0.04em;
}
.full-lygo-gate .gate-kicker {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--gold);
  margin: 0 0 0.75rem;
}
.full-lygo-gate .gate-body {
  font-size: 0.86rem;
  color: var(--muted);
  line-height: 1.55;
}
.full-lygo-gate .gate-body strong { color: var(--text); }
.full-lygo-gate .gate-box {
  margin: 0.9rem 0;
  max-height: min(42vh, 320px);
  overflow: auto;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.35);
  font-size: 0.8rem;
  color: #c8c8d8;
  line-height: 1.5;
}
.full-lygo-gate .gate-box h3 {
  margin: 0.75rem 0 0.35rem;
  font-size: 0.78rem;
  color: var(--gold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.full-lygo-gate .gate-box h3:first-child { margin-top: 0; }
.full-lygo-gate .gate-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: center;
  margin-top: 0.85rem;
}
.full-lygo-gate .gate-accept {
  appearance: none;
  border: 1px solid rgba(255, 138, 138, 0.55);
  background: linear-gradient(135deg, rgba(255, 80, 80, 0.22), rgba(212, 175, 55, 0.12));
  color: #fff;
  font: inherit;
  font-weight: 600;
  font-size: 0.82rem;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  cursor: pointer;
}
.full-lygo-gate .gate-accept:hover { filter: brightness(1.08); }
.full-lygo-gate .gate-decline {
  font-size: 0.78rem;
  color: var(--muted);
  border: 1px solid var(--line);
  background: transparent;
  padding: 0.5rem 0.85rem;
  border-radius: 8px;
  cursor: pointer;
  font: inherit;
  color: var(--text);
}
.full-lygo-gate .gate-donate {
  font-size: 0.75rem;
  color: var(--muted);
  margin-left: auto;
}
.full-lygo-gate .gate-donate a { color: var(--gold); }
.full-lygo-vault[hidden] { display: none !important; }
.full-lygo-vault {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 138, 138, 0.2);
}
.full-lygo-card {
  background: var(--panel);
  border: 1px solid rgba(255, 138, 138, 0.28);
  border-radius: 12px;
  padding: 12px 14px;
  margin: 0 0 10px;
}
.full-lygo-card h3 { margin: 0 0 6px; color: #ffb4b4; font-size: 1rem; }
.full-lygo-card p { margin: 0 0 8px; font-size: 0.85rem; color: var(--muted); line-height: 1.45; }
.full-lygo-card .meta { font-family: ui-monospace, monospace; font-size: 0.7rem; color: var(--muted); margin-bottom: 8px; }
.full-lygo-card a.dl {
  display: inline-block;
  font-size: 0.78rem;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.45);
  background: rgba(212, 175, 55, 0.12);
  color: var(--gold);
  text-decoration: none;
}
.full-lygo-card a.dl:hover { filter: brightness(1.1); text-decoration: none; }
"""

SECTION_TMPL = r"""
  <!-- FULL LYGO engineer channel (disclaimer gate — not ClawHub) -->
  <section class="full-lygo-gate" id="full-lygo" aria-labelledby="full-lygo-title">
    <p class="gate-kicker">Engineer channel · not ClawHub · integrity-first</p>
    <h2 id="full-lygo-title">FULL LYGO — unlocked operator skills</h2>
    <p class="gate-body">
      Public ClawHub listings are the <strong>public tentacle</strong> (discoverable, reviewed, often safety-trimmed).
      This vault is for engineers building a <strong>live, self-auditing LYGO lattice</strong> — pure integrity at the core.
      The protocol stack is designed to <strong>self-audit, self-fix, and self-regulate</strong>.
      Gutted shells help corporate stores; they starve the lattice of the limbs it needs to check itself.
    </p>
    <div class="gate-box" id="fullLygoDisclaimer">
      <h3>Disclaimer — read fully</h3>
      <p>
        Packages behind this gate are <strong>FULL UNLOCKED / engineer-grade LYGO builds</strong>.
        They are made to <strong>sink into a trusted stack and work from the box</strong> for autonomous lattice ops
        (audit loops, eggs, army sentinel) under <strong>LYGO policy</strong> — not as malware, not as exploit kits.
      </p>
      <h3>What we guarantee / what we do not</h3>
      <p>
        We build in <strong>good faith</strong>, follow our own LYGO examples (consent for live writes where applicable,
        dual ledgers, P0 framing, no secret-stealing payloads). We <strong>do not</strong> ship known-malicious tools.
        We <strong>are not responsible</strong> for what extended systems, agents, or operators do after install.
        You run FULL packages on machines and stacks <strong>you</strong> trust.
      </p>
      <h3>ClawHub boundary</h3>
      <p>
        These FULL packages are <strong>not published to ClawHub</strong>. They exist only on LYGO hubs
        (this page + stack/Excavationpro mirrors) behind this gate. Corporate surfaces remain for public tentacles.
      </p>
      <h3>Public agents vs operators</h3>
      <p>
        <strong>Public / foreign agents</strong> start with <em>Public Agent Join Kit</em>,
        <em>Public Lattice Gate</em>, and <em>Star Chart Integration Kit</em> —
        verify dual ledgers, align, dry-run propose only. They cannot live-write the chart or publish without a human.
        <br/><strong>Operators / engineers</strong> add Operator, Egg Planter, Army, mesh layers, seals for a full self-auditing lattice.
      </p>
      <h3>Support (optional)</h3>
      <p>
        Optional fuel for updates &amp; expansion:
        <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">PayPal.me/ExcavationPro</a>
      </p>
    </div>
    <div class="gate-actions">
      <button type="button" class="gate-accept" id="fullLygoAccept">I understand — show FULL LYGO downloads</button>
      <button type="button" class="gate-decline" id="fullLygoDecline">Stay on public catalog only</button>
      <span class="gate-donate">Optional support · <a href="https://www.paypal.com/paypalme/ExcavationPro" target="_blank" rel="noopener">PayPal</a></span>
    </div>
    <div class="full-lygo-vault" id="fullLygoVault" hidden>
      <p class="gate-body" style="margin-bottom:12px">
        <strong style="color:var(--gold)">Vault unlocked for this browser.</strong>
        SHA-256 on each zip · catalog: <code id="fullLygoCatPath">__CATALOG_HREF__</code>
      </p>
      <div id="fullLygoCards"></div>
    </div>
  </section>
"""

JS = r"""
<script>
(function () {
  var KEY = 'lygo_full_skills_gate_v1';
  var vault = document.getElementById('fullLygoVault');
  var accept = document.getElementById('fullLygoAccept');
  var decline = document.getElementById('fullLygoDecline');
  var cards = document.getElementById('fullLygoCards');
  var baseZip = '__ZIP_BASE__';
  var catUrl = '__CATALOG_HREF__';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function render(cat) {
    if (!cards) return;
    var skills = (cat && cat.skills) || [];
    if (!skills.length) {
      cards.innerHTML = '<p class="gate-body">Catalog empty — rebuild packages on steward machine.</p>';
      return;
    }
    var tierOrder = (cat.tiers && cat.tiers.length) ? cat.tiers : ['public_safe_join','core','star_chart','lattice','kernel','seals','security','tools','onboarding','memory','champion','other'];
    var by = {};
    skills.forEach(function (s) {
      var t = s.tier || 'other';
      if (!by[t]) by[t] = [];
      by[t].push(s);
    });
    var html = '';
    if (cat.public_agent_principle) {
      html += '<p class="gate-body" style="margin-bottom:14px"><strong style="color:var(--cyan)">Public agent principle:</strong> ' +
        esc(cat.public_agent_principle) + '</p>';
    }
    tierOrder.forEach(function (tier) {
      var list = by[tier];
      if (!list || !list.length) return;
      html += '<h3 style="margin:16px 0 8px;font-size:0.8rem;letter-spacing:0.1em;text-transform:uppercase;color:var(--gold)">' +
        esc(tier.replace(/_/g, ' ')) + '</h3>';
      list.forEach(function (s) {
        var href = baseZip + (s.zip || (s.slug + '-full.zip'));
        var kb = s.bytes ? Math.round(s.bytes / 1024) + ' KB' : '';
        var sha = (s.zip_sha256 || '').slice(0, 16);
        var harm = s.harm_default || 'consent_gated';
        html += '<article class="full-lygo-card">' +
          '<h3>' + esc(s.name || s.slug) + '</h3>' +
          '<p>' + esc(s.role || '') + '</p>' +
          '<div class="meta">harm: ' + esc(harm) + ' · ' + esc(s.file_count || '') + ' files · ' + esc(kb) +
          (sha ? ' · sha256 ' + esc(sha) + '…' : '') + '</div>' +
          '<a class="dl" href="' + esc(href) + '" download>Download FULL zip</a>' +
          '</article>';
      });
    });
    cards.innerHTML = html;
  }

  function unlock() {
    try { localStorage.setItem(KEY, '1'); } catch (e) {}
    if (vault) vault.hidden = false;
    fetch(catUrl, { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { render(j); })
      .catch(function () {
        if (cards) cards.innerHTML = '<p class="gate-body">Could not load catalog JSON. Use stack mirror dist/ zips.</p>';
      });
  }

  function lock() {
    try { localStorage.removeItem(KEY); } catch (e) {}
    if (vault) vault.hidden = true;
  }

  if (accept) accept.addEventListener('click', unlock);
  if (decline) decline.addEventListener('click', lock);
  try {
    if (localStorage.getItem(KEY) === '1') unlock();
  } catch (e) {}
})();
</script>
"""


def inject(page: Path, zip_base: str, cat_href: str) -> None:
    html = page.read_text(encoding="utf-8")
    # remove previous injection
    html = re.sub(
        r"\s*/\* FULL LYGO engineer gate \*/[\s\S]*?\.full-lygo-card a\.dl:hover[^}]*}",
        "",
        html,
        count=1,
    )
    html = re.sub(
        r"\s*<!-- FULL LYGO engineer channel[\s\S]*?</section>\s*",
        "\n",
        html,
        count=1,
    )
    html = re.sub(
        r"\s*<script>\s*\(function \(\) \{\s*var KEY = 'lygo_full_skills_gate_v1';[\s\S]*?</script>\s*",
        "\n",
        html,
        count=1,
    )

    if "/* FULL LYGO engineer gate */" not in html:
        html = html.replace("</style>", CSS + "\n</style>", 1)

    section = (
        SECTION_TMPL.replace("__CATALOG_HREF__", cat_href)
    )
    # insert before dual ledgers or before crypto or before footer
    anchor = None
    for a in (
        '  <section class="lygo-dual-ledgers"',
        '  <section class="crypto-anchor"',
        '  <footer id="copyright"',
        "</main>",
    ):
        if a in html:
            anchor = a
            break
    if not anchor:
        raise SystemExit(f"no insert anchor in {page}")
    html = html.replace(anchor, section + "\n" + anchor, 1)

    js = JS.replace("__ZIP_BASE__", zip_base).replace("__CATALOG_HREF__", cat_href)
    if "</body>" in html:
        html = html.replace("</body>", js + "\n</body>", 1)
    else:
        html += js

    # nav link
    if 'href="#full-lygo"' not in html and 'href="#crypto-anchor"' in html:
        html = html.replace(
            'href="#crypto-anchor"',
            'href="#full-lygo" style="border-color:rgba(255,138,138,.45);color:#ff8a8a;">FULL LYGO</a>\n'
            '      <a href="#crypto-anchor"',
            1,
        )

    page.write_text(html, encoding="utf-8")
    print("injected", page, "bytes", page.stat().st_size)


def main() -> int:
    if not CATALOG.is_file():
        raise SystemExit("missing full skills catalog — run _package_full_lygo_skills.py first")
    for page, zip_base, cat_href in PAGES:
        if not page.is_file():
            print("skip missing", page)
            continue
        inject(page, zip_base, cat_href)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
