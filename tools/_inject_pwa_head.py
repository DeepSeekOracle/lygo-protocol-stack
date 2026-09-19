from pathlib import Path
p = Path(r"I:\E Drive\Excavationpro\excavationpro-listen.html")
t = p.read_text(encoding="utf-8")
ins = """<link rel="manifest" href="manifest-listen.webmanifest">
<meta name="theme-color" content="#0a0a12">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Excavationpro">
<link rel="apple-touch-icon" href="assets/listen-icon-512.svg">
"""
if "manifest-listen.webmanifest" not in t.split("<script", 1)[0]:
    t = t.replace("</head>", ins + "</head>", 1)
    p.write_text(t, encoding="utf-8")
    print("head injected")
else:
    print("head ok")
docs = Path(r"I:\E Drive\lygo-protocol-stack\docs\excavationpro-listen.html")
docs.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
print("docs synced", len(p.read_text(encoding="utf-8")))
