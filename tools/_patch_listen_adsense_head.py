from pathlib import Path
p = Path(r"I:/E Drive/Excavationpro/excavationpro-listen.html")
h = p.read_text(encoding="utf-8")
head, rest = h.split("</head>", 1)
meta = '<meta name="google-adsense-account" content="ca-pub-0646320966060599">'
script = (
    '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0646320966060599"\n'
    '     crossorigin="anonymous"></script>'
)
if "adsbygoogle.js?client=ca-pub-0646320966060599" not in head:
    if meta in head:
        head = head.replace(meta, meta + "\n" + script, 1)
        print("injected script after meta")
    else:
        head = head.replace("<head>", "<head>\n" + meta + "\n" + script, 1)
        print("injected meta+script")
else:
    print("script already in head")
h = head + "</head>" + rest
h = h.replace("play-listing.js?v=4", "play-listing.js?v=5")
h = h.replace("play-listing.js?v=3", "play-listing.js?v=5")
p.write_text(h, encoding="utf-8")
print("v5", "play-listing.js?v=5" in h)
print("head has script", "adsbygoogle.js?client=ca-pub" in head)
