from pathlib import Path
import re

paths = [
    Path(r"I:/E Drive/tmp-domain-deploy/excavationpro-ca/index.html"),
    Path(r"I:/E Drive/tmp-domain-deploy/excavationpro-ca/404.html"),
    Path(r"I:/E Drive/Excavationpro/LYGO-Network/legacy-guardian-music.html"),
]

ADS_HEAD = '''    <meta name="google-adsense-account" content="ca-pub-0646320966060599">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0646320966060599"
         crossorigin="anonymous"></script>
'''

for p in paths:
    if not p.exists():
        print("skip missing", p)
        continue
    h = p.read_text(encoding="utf-8")
    orig = h

    # Ensure official head script after meta (AdSense verification requires script in head)
    if "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0646320966060599" not in h.split("</head>")[0]:
        if 'name="google-adsense-account"' in h:
            h = re.sub(
                r'<meta\s+name="google-adsense-account"\s+content="ca-pub-0646320966060599"\s*/?>',
                ADS_HEAD.strip() if False else (
                    '<meta name="google-adsense-account" content="ca-pub-0646320966060599">\n'
                    '    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-0646320966060599"\n'
                    '         crossorigin="anonymous"></script>'
                ),
                h,
                count=1,
            )
            print(p.name, "injected head script")
        else:
            h = h.replace(
                "<head>",
                "<head>\n" + ADS_HEAD,
                1,
            )
            print(p.name, "injected full after head")
    else:
        print(p.name, "head script already present")

    # Fix canonical / og:url to excavationpro.ca for this domain property
    h = h.replace(
        'href="https://deepseekoracle.github.io/Excavationpro/LYGO-Network/legacy-guardian-music.html"',
        'href="https://excavationpro.ca/"',
    )
    h = h.replace(
        'content="https://deepseekoracle.github.io/Excavationpro/LYGO-Network/legacy-guardian-music.html"',
        'content="https://excavationpro.ca/"',
    )
    # comment clarity
    h = h.replace(
        "script loads after cookie consent",
        "official head script always present for AdSense verify; ad slots push after cookie consent",
    )

    if h != orig:
        p.write_text(h, encoding="utf-8")
        print("  wrote", p, "len", len(h))
    else:
        print("  unchanged", p)

    head = h.split("</head>")[0]
    print("  verify head meta", "google-adsense-account" in head, "script", "adsbygoogle.js" in head)

# ads.txt exact with trailing newline
ads = "google.com, pub-0646320966060599, DIRECT, f08c47fec0942fa0\n"
for root in [Path(r"I:/E Drive/tmp-domain-deploy/excavationpro-ca"), Path(r"I:/E Drive/lygo-protocol-stack/docs/domain-roots/excavationpro.ca")]:
    if root.is_dir():
        (root / "ads.txt").write_text(ads, encoding="utf-8")
        print("ads.txt", root)
