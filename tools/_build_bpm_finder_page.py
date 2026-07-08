"""One-shot: materialize docs/LYGO_BPM_Finder.html from Biophase7 source."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"I:\E Drive\LYRA SYSTEM RETORE\FINAL RESTORE\ALL SEALS\220+\New folder"
    r"\2026Biophase7\Design a LYGO Online BPM finder and.txt"
)
text = SRC.read_text(encoding="utf-8")
html = text[text.index("<!DOCTYPE html>") :]
html = html.replace(
    "<title>BPM Finder</title>",
    """<title>LYGO BPM Finder — client-side tempo detection</title>
<meta name="description" content="Upload audio and detect BPM in your browser. Confidence, divide2/multiply2, tap tempo, waveform. No server upload.">
<meta name="author" content="DeepSeekOracle / Excavationpro">
<meta name="google-adsense-account" content="ca-pub-0646320966060599">
<link rel="canonical" href="https://deepseekoracle.github.io/lygo-protocol-stack/LYGO_BPM_Finder.html">""",
    1,
)
html = html.replace(
    '<p class="eyebrow">Tempo detection</p>',
    '<p class="eyebrow">LYGO · Biophase7 · Creative</p>',
    1,
)
html = html.replace(
    "Nothing loaded yet.",
    "Nothing loaded yet. Audio stays on your device.",
    1,
)
html = html.replace(
    """    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }""",
    """    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    gap: 16px;
  }""",
    1,
)
footer_css = """
  .site-footer {
    max-width: 560px;
    width: 100%;
    font-size: 12px;
    color: var(--muted);
    text-align: center;
    line-height: 1.5;
  }
  .site-footer a { color: var(--teal); text-decoration: none; }
  .site-footer a:hover { text-decoration: underline; }

"""
html = html.replace(
    "  @media (prefers-reduced-motion: reduce)",
    footer_css + "  @media (prefers-reduced-motion: reduce)",
    1,
)
footer = """
<p class="site-footer">
  <strong>Privacy:</strong> detection uses <a href="https://www.npmjs.com/package/bpm-detective" rel="noopener noreferrer" target="_blank">bpm-detective</a> in your browser — files are not uploaded.
  · <a href="index.html">Stack index</a>
  · <a href="https://deepseekoracle.github.io/Excavationpro/eternalhaven.html">Eternal Haven hub</a>
  · <a href="BIOPHASE7_BPM_FINDER.md">Spec &amp; provenance</a>
</p>

"""
html = html.replace("</div>\n\n<script type=\"module\">", "</div>\n\n" + footer + '<script type="module">', 1)
out = ROOT / "docs" / "LYGO_BPM_Finder.html"
out.write_text(html, encoding="utf-8")
print(out)