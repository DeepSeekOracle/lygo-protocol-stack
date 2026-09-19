from distrokid_vault_browser_scrape import CDP, pick_page

page = pick_page("distrokid")
print("page", page.get("url"))
cdp = CDP(page["webSocketDebuggerUrl"])
cdp.call("Page.enable")
cdp.call("Runtime.enable")
print("url", cdp.eval("location.href"))
print("title", cdp.eval("document.title"))
text = cdp.eval("document.body ? document.body.innerText.slice(0, 1200) : ''")
print("text sample:\n", text)
n = cdp.eval("document.querySelectorAll('a[href*=\"vault/file\"]').length")
print("vault/file links:", n)
# any links with vault
n2 = cdp.eval(
    "Array.from(document.querySelectorAll('a[href]')).map(a=>a.href).filter(h=>h.includes('vault')).slice(0,20)"
)
print("vault hrefs sample:", n2)
cdp.close()
