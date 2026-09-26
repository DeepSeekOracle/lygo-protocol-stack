/* LYGO SkillHub — the supporter gate on the download buttons.

   What this is. Every download button on this page (the installer `.exe`s, the multi-file sets)
   asks for the member code that supporters get from the Patreon member section. The code is
   checked here in your browser against a SHA-256 in this file. Nothing else on the page is
   gated: the ClawHub skills, the install notes, the hashes and the copy all stay open.

   What this is not, said plainly. It is a thank-you gate, not a licence and not DRM. It proves
   "you were given this month's code" and nothing more — anything a browser can check, a
   determined visitor can bypass, and the build files themselves are public on Hugging Face.
   Supporting the work is what keeps the builds coming; this gate is the ask, not a lock.

   The same system as the portal and the arcade, deliberately:
     * the table below is the SAME table portal/supporter.js carries, and it is written by
       portal/supporter/rotate.py and copied here by tools/sync_supporter_codes.py — the tool is
       the only writer, so the copies cannot drift;
     * the unlock is stored under the SAME key (lygo_portal_supporter), so one code entered
       anywhere on the site — the portal, a game, this page — unlocks everywhere in this browser;
     * the same normalising rule (upper-case, and only A-Z0-9 counts) means dashes, spaces and
       case do not matter to a supporter typing it;
     * the same expiry rule: each entry runs to the 5th of the following month, so an honest
       supporter is never turned away on rotation day.

   The plaintext code is never stored here or in the browser: localStorage keeps only
   {label, until, at}.
   Generated table: portal/supporter/rotate.py — do not hand-edit. */
(function (g, d) {
  "use strict";

  var UNLOCK_STORE = "lygo_portal_supporter";     // the portal's key: one unlock, whole site
  var GATE_VERSION = "2026-09-26";
  var PATREON = "https://www.patreon.com/Excavationpro/posts/lygo-supporter-170485961";
  var PAYPAL = "https://www.paypal.com/paypalme/ExcavationPro";
  var VAULT = "huggingface.co/DeepSeekOracle/lygo-console-builds/";
  var VAULT_PARTS = ["/resolve/", "/tree/"];      // artifact files and multi-file sets
  /* Not every download button lives in the build vault: the USB kits are served from the project's
     own /downloads/ path. So an artifact by extension counts too — but only on the project's own
     hosts or the vault, and only for real artifacts, so a README or a note is never gated. */
  var ARTIFACT = /\.(exe|bin|zip|7z|dmg|iso|msi|tar|gz|whl|pkg)($|[?#])/i;
  var ARTIFACT_HOSTS = ["deepseekoracle.github.io/", "chatagent.ca/", "huggingface.co/DeepSeekOracle/"];

/* @supporter-hashes:start */
  var CODE_HASHES = [
    {"label": "2026-08", "sha256": "5d29c090b2e2ee7796cc7cbbffa78ec50544cc1e45df8e9224b557704fcf0f5d", "until": "2026-09-05", "note": "rotated out"},
    {"label": "2026-09", "sha256": "31f34f39b74ad94630e9b2c8ebceb64660ea5546b83d9f88447523eb73498990", "until": "2026-10-05", "note": "this month's code"},
    {"label": "steward", "sha256": "9dc55ba3412edfbaedd8c62140cb23168bb613934983f8c4b7337f36f3026e16", "until": null, "permanent": true, "note": "steward: never expires \u2014 keep the plaintext private"},
    {"label": "2026-10", "sha256": "317714cd0c62c304d7eed6950347d44c1a8cf1f5588c098f41034cf9715ddd4f", "until": "2026-11-05", "note": "monthly rotation"},
    {"label": "2026-11", "sha256": "44cfbab3d9f3cb32c9c0164f14b0816af30be6c2b2958e4a7f47c16d011e354c", "until": "2026-12-05", "note": "monthly rotation"},
    {"label": "2026-12", "sha256": "4bba660370693a8c8ea242d17636d75321aa8f34819751214e76492babc37e76", "until": "2027-01-05", "note": "monthly rotation"},
    {"label": "2027-01", "sha256": "ff580f4a38fbf99c778b6bd1540913b716319cda4a9ab1b1d8cddc183920d3f9", "until": "2027-02-05", "note": "monthly rotation"},
    {"label": "2027-02", "sha256": "8a2b17eb5d47f99ac31393749a89e3653c77e34e35bc9125ae0a88d8e87c1844", "until": "2027-03-05", "note": "monthly rotation"},
    {"label": "2027-03", "sha256": "68c1cddefbffe22dd8d98f751bfee479b1084606aafaa47f17b94fe120107191", "until": "2027-04-05", "note": "monthly rotation"},
    {"label": "2027-04", "sha256": "626954aa4d23ce0a57acfa71fd8f4bab99d37eab6cee70f1b0b5e092a12fd49b", "until": "2027-05-05", "note": "monthly rotation"},
    {"label": "2027-05", "sha256": "c57c9f6f92f4c3888d1c1060ae300046deffef378ca5e6e54ce582a8b0e118bf", "until": "2027-06-05", "note": "monthly rotation"},
    {"label": "2027-06", "sha256": "10de61edec644146fd74a8c25bd61d1ad7320cee64c99c99be5b7d43bf2888fc", "until": "2027-07-05", "note": "monthly rotation"},
    {"label": "2027-07", "sha256": "6859a1071fa89e4ef5f4c7444947fb80ad88c90673a7c21ba8109d9aa495b0bf", "until": "2027-08-05", "note": "monthly rotation"},
    {"label": "2027-08", "sha256": "d27ac913e99bc83337a4c0f1e367329ca02141244c60df358b24828e187252b0", "until": "2027-09-05", "note": "monthly rotation"},
    {"label": "2027-09", "sha256": "10c5e57eb30e266128bfe2b224033f4b158f7e841cd3897a67237f1a0a8ecb13", "until": "2027-10-05", "note": "monthly rotation"},
    {"label": "2027-10", "sha256": "95d773b07ab019a8911892c26e883caf7e6532142a7e54335ebef3d7d2b1a11e", "until": "2027-11-05", "note": "monthly rotation"},
    {"label": "2027-11", "sha256": "01bf25a5fb3eb1fddd0750bfd0dd1d63759ce9deb59dda78e775116fafbab391", "until": "2027-12-05", "note": "monthly rotation"},
    {"label": "2027-12", "sha256": "93959640b22345b749a16a1d438961674e7e4a84cbeaf145bbf72890f66f27f4", "until": "2028-01-05", "note": "monthly rotation"},
    {"label": "2028-01", "sha256": "65861f7114d22d781add12ed799944df55047bafdcbd65099db3a3733026a4ba", "until": "2028-02-05", "note": "monthly rotation"},
    {"label": "2028-02", "sha256": "44c14568c6b534f325214a9291867ac77c5ba98067123b28ca39da4a1b4cbe21", "until": "2028-03-05", "note": "monthly rotation"},
    {"label": "2028-03", "sha256": "bbd85e479153d76a5d437916ee8f5614cfea3858b9ae8b3918f53e7af7e47a8e", "until": "2028-04-05", "note": "monthly rotation"},
    {"label": "2028-04", "sha256": "dbd8eed19924425f889992af55052256976f6fccc94a813ad840ad06647aeac2", "until": "2028-05-05", "note": "monthly rotation"},
    {"label": "2028-05", "sha256": "feff0d5a91086f9ea175342e766b2f81bd7c6499fe708b1f7a23666acd857235", "until": "2028-06-05", "note": "monthly rotation"},
    {"label": "2028-06", "sha256": "42e16c90fd05ec9290f41a7bf7d0965872ab7f87c86f4d7310778e4f0f4c94a0", "until": "2028-07-05", "note": "monthly rotation"},
    {"label": "2028-07", "sha256": "e17b51d928f7c9ea00a1e8691764b0dfbfc8921beb29e179599fc943240f0cd3", "until": "2028-08-05", "note": "monthly rotation"},
    {"label": "2028-08", "sha256": "440c5ab94352de12addf10ce37bc36724ab4297ddac5ceb38cc2d93b77cee971", "until": "2028-09-05", "note": "monthly rotation"},
    {"label": "2028-09", "sha256": "cae24e52d1271aabe19e21cd4a0cb3c90ef02956b0e82be3e1eefab208fc0fef", "until": "2028-10-05", "note": "monthly rotation"},
    {"label": "2028-10", "sha256": "82f239c06c7170624b25e81a6ab0d655cb0e1fc90059275a8488bce267119f03", "until": "2028-11-05", "note": "monthly rotation"},
    {"label": "2028-11", "sha256": "18aadac7c4bb4f7427d5a27eaea20d58a062f8a2b88e01c89f8b8fb7217a4309", "until": "2028-12-05", "note": "monthly rotation"},
    {"label": "2028-12", "sha256": "ebf7e1c300b9a5f48a158e39cfb3e239db961b262588340db8cd5e5c595223df", "until": "2029-01-05", "note": "monthly rotation"},
    {"label": "2029-01", "sha256": "e1a17c13eab698c08c3810ba46d451c591999396899baab5516c81e29fb0947a", "until": "2029-02-05", "note": "monthly rotation"},
    {"label": "2029-02", "sha256": "9cbd1c7dd297e89f4f5f889572ff89ba802b46a977a5b873e64dd827367a4400", "until": "2029-03-05", "note": "monthly rotation"},
    {"label": "2029-03", "sha256": "1d97297008142bf08bb5a02624d2c25b5252c335fadd2bfce089a4887d69c884", "until": "2029-04-05", "note": "monthly rotation"}
  ];
  /* @supporter-hashes:end */

  var layer = null, cardEl = null, inputEl = null, goEl = null, msgEl = null, contEl = null;
  var pendingHref = "", lastFocus = null, prevOverflow = "", wired = false;

  function el(id) { return d.getElementById(id); }
  function qsa(sel, root) {
    return Array.prototype.slice.call((root || d).querySelectorAll(sel));
  }
  function store(k) { try { return g.localStorage.getItem(k); } catch (_) { return null; } }
  function save(k, v) { try { g.localStorage.setItem(k, String(v)); } catch (_) {} }
  function drop(k) { try { g.localStorage.removeItem(k); } catch (_) {} }

  function normalize(code) { return String(code || "").toUpperCase().replace(/[^A-Z0-9]/g, ""); }
  function endOfDay(day) { var t = new Date(String(day) + "T23:59:59"); return isNaN(t.getTime()) ? 0 : t.getTime(); }

  function sha256hex(text) {
    if (!g.crypto || !g.crypto.subtle) throw new Error("no_webcrypto");
    return g.crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) {
        return ("0" + b.toString(16)).slice(-2);
      }).join("");
    });
  }

  function record() {
    var raw = store(UNLOCK_STORE);
    if (!raw) return null;
    try { var r = JSON.parse(raw); return (r && typeof r === "object") ? r : null; } catch (_) { return null; }
  }

  /* state(): what the browser remembers, judged against today. A lapsed record stays readable
     long enough to say which date it ran out on — that is the rotation showing itself. */
  function state() {
    var r = record();
    if (!r) return { unlocked: false, label: "", until: "", lapsed: false };
    var live = !r.until || Date.now() <= endOfDay(r.until);
    return {
      unlocked: live, label: String(r.label || ""), until: String(r.until || ""),
      lapsed: !live && !!r.until
    };
  }

  function tryCode(code) {
    var n = normalize(code);
    if (n.length < 12) {
      return Promise.resolve({ ok: false, why: "That looks too short. The code looks like LYGO-2609-XXXX-XXXX." });
    }
    return sha256hex(n).then(function (h) {
      var hit = null, i;
      for (i = 0; i < CODE_HASHES.length; i++) {
        if (CODE_HASHES[i].sha256 === h) { hit = CODE_HASHES[i]; break; }
      }
      if (!hit) {
        return { ok: false, why: "That code is not one of this site's codes. Codes rotate every month — the current one is in the Patreon member section." };
      }
      if (!hit.permanent && hit.until && Date.now() > endOfDay(hit.until)) {
        return { ok: false, why: "That code was valid through " + hit.until + " and has been rotated out. This month's code is in the Patreon member section." };
      }
      save(UNLOCK_STORE, JSON.stringify({
        label: hit.label, until: hit.permanent ? "" : (hit.until || ""), at: new Date().toISOString()
      }));
      return { ok: true, label: hit.label, until: hit.permanent ? "" : (hit.until || "") };
    }, function () {
      return { ok: false, why: "This browser will not hash outside a secure page (https). The live page is https." };
    });
  }

  /* ---- which buttons are gated --------------------------------------------------------
     By href, not by hand-marking: anything on this page pointing into the build vault at a
     file (resolve) or a multi-file set (tree) is a download. The install notes and the hash
     lists (blob) are information and stay open, as do the ClawHub links. */
  function gatedHref(href) {
    if (!href) return false;
    var h = String(href), i;
    if (h.indexOf(VAULT) !== -1) {                       // the build vault: files and sets
      for (i = 0; i < VAULT_PARTS.length; i++) {
        if (h.indexOf(VAULT_PARTS[i]) !== -1) return true;
      }
    }
    if (ARTIFACT.test(h)) {                              // an artifact file, on our own ground
      /* A relative path is this site's own file — the console page links its kits as
         `data/.../kit.zip`, which no host list would ever match. */
      if (h.charAt(0) === "/" || h.indexOf("://") === -1) return true;
      for (i = 0; i < ARTIFACT_HOSTS.length; i++) {
        if (h.indexOf(ARTIFACT_HOSTS[i]) !== -1) return true;
      }
    }
    return false;
  }
  function anchorOf(node) {
    var n = node;
    while (n && n !== d) {
      if (n.nodeType === 1 && n.tagName && n.tagName.toLowerCase() === "a" && n.getAttribute) return n;
      n = n.parentNode;
    }
    return null;
  }
  function isGated(node) {
    var a = anchorOf(node);
    return !!a && gatedHref(a.getAttribute("href"));
  }
  /* A pure predicate, so the gate can be tested without starting a build download. */
  function wouldBlock(node) { return isGated(node) && !state().unlocked; }

  /* ---- the page's own state line and lock pills --------------------------------------- */
  function paint() {
    var on = state().unlocked, st = state(), i;
    var anchors = qsa("a[href]");
    for (i = 0; i < anchors.length; i++) {
      var a = anchors[i];
      if (layer && layer.contains(a)) continue;   // the modal's own links are not page buttons
      if (!gatedHref(a.getAttribute("href"))) continue;
      a.setAttribute("data-lyg-gated", "1");
      if (on) {
        a.classList.remove("lyg-locked");
        a.removeAttribute("title");
      } else {
        a.classList.add("lyg-locked");
        a.setAttribute("title", "Supporter code required — this month's code is in the Patreon member section");
      }
    }
    var text = on
      ? ("Unlocked in this browser" + (st.until ? " · valid through " + st.until : " · steward code") +
         " — every download button works.")
      : ((st.lapsed ? "Your code lapsed on " + st.until + ". " : "") +
         "The download buttons below ask for this month's member code. Everything else on this page stays open.");
    qsa("[data-lyg-gate-state]").forEach(function (n) { n.textContent = text; });
    qsa("[data-lyg-gate-chip]").forEach(function (n) { n.hidden = !on; });
    qsa("[data-lyg-gate-relock]").forEach(function (n) { n.hidden = !on; });
    qsa("[data-lyg-gate-open]").forEach(function (n) {
      n.textContent = on ? "Supporter state" : "I have a code";
    });
    try { d.dispatchEvent(new CustomEvent("lygo-supporter", { detail: st })); } catch (_) {}
  }

  /* ---- the modal ----------------------------------------------------------------------- */
  function build() {
    if (layer) return;
    layer = d.createElement("div");
    layer.className = "lyg-layer";
    layer.id = "lygGateLayer";
    layer.setAttribute("role", "dialog");
    layer.setAttribute("aria-modal", "true");
    layer.setAttribute("aria-labelledby", "lygGateTitle");
    layer.hidden = true;
    layer.innerHTML =
      '<div class="lyg-card" role="document">' +
      '  <button type="button" class="lyg-close" id="lygGateClose" aria-label="Close">\u00d7</button>' +
      '  <p class="lyg-kicker">Supporter downloads \u00b7 LYGO build vault</p>' +
      '  <h2 class="lyg-title" id="lygGateTitle">One code unlocks the download buttons</h2>' +
      '  <p class="lyg-lead" id="lygGateFor"></p>' +
      '  <p class="lyg-lead">The installers and the multi-file sets are what the supporter code is for. ' +
      'Get <strong>this month\u2019s code</strong> from the <strong>Patreon member section</strong> \u2014 it rotates monthly, ' +
      'so an old code stops working on the 5th.</p>' +
      '  <ul class="lyg-list">' +
      '    <li><strong>Free, always:</strong> the ClawHub skills, the install notes, every SHA-256, and all the reading on this page.</li>' +
      '    <li><strong>Code required:</strong> the download buttons \u2014 that is the whole gate.</li>' +
      '    <li><strong>Honest terms:</strong> the code is checked in your browser, so it is a thank-you gate and not a lock. The build files are also public on Hugging Face. Supporting us is what funds these consoles.</li>' +
      '    <li><strong>Per browser:</strong> the unlock lives in this browser only, until the code\u2019s expiry date.</li>' +
      '  </ul>' +
      '  <div class="lyg-field">' +
      '    <label class="lyg-label" for="lygGateCode">Member code</label>' +
      '    <input id="lygGateCode" class="lyg-input" type="text" inputmode="latin" autocomplete="off" ' +
      'spellcheck="false" placeholder="LYGO-2609-XXXX-XXXX">' +
      '  </div>' +
      '  <div class="lyg-actions">' +
      '    <button id="lygGateGo" class="lyg-btn lyg-btn-cta" type="button">Unlock downloads</button>' +
      '    <a class="lyg-btn lyg-btn-door" id="lygGateGet" href="' + PATREON + '" target="_blank" rel="noopener">Get this month\u2019s code on Patreon \u2192</a>' +
      '    <a class="lyg-btn lyg-btn-door" id="lygGatePay" href="' + PAYPAL + '" target="_blank" rel="noopener">Or support with PayPal \u2192</a>' +
      '    <button id="lygGateRelock" class="lyg-btn lyg-btn-quiet" type="button" hidden>Lock again in this browser</button>' +
      '  </div>' +
      '  <p class="lyg-msg" id="lygGateMsg" role="status" aria-live="polite"></p>' +
      '  <p class="lyg-foot">The code is never stored \u2014 this browser keeps only the month it unlocked.</p>' +
      '</div>';
    d.body.appendChild(layer);

    inputEl = el("lygGateCode"); goEl = el("lygGateGo"); msgEl = el("lygGateMsg");
    contEl = el("lygGateFor");

    el("lygGateClose").addEventListener("click", close);
    el("lygGateRelock").addEventListener("click", function () {
      relock();
      if (msgEl) msgEl.textContent = "Locked again in this browser. The download buttons ask for a code.";
    });
    goEl.addEventListener("click", submit);
    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); submit(); }
    });
    layer.addEventListener("click", function (e) { if (e.target === layer) close(); });
    d.addEventListener("keydown", function (e) {
      if (layer.hidden) return;
      if (e.key === "Escape") { close(); return; }
      if (e.key !== "Tab") return;
      var f = qsa('a[href], button:not([disabled]), input:not([disabled])', layer)
        .filter(function (n) { return n.offsetParent !== null; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && d.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && d.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  function open(href, label, fromRow) {
    build();
    pendingHref = href || "";
    var st = state();
    if (contEl) {
      contEl.textContent = href
        ? ("You asked for: " + (label || "a build download") + " \u2014 enter the code and the button works.")
        : "Enter this month\u2019s member code to unlock every download button on this page.";
    }
    if (msgEl) {
      msgEl.textContent = st.unlocked
        ? ("Already unlocked in this browser" + (st.until ? " \u2014 valid through " + st.until + "." : "."))
        : (st.lapsed ? "Your last code lapsed on " + st.until + ". This month\u2019s code is on the Patreon post." : "");
    }
    if (goEl) goEl.textContent = st.unlocked ? "Unlock again" : "Unlock downloads";
    if (el("lygGateRelock")) el("lygGateRelock").hidden = !st.unlocked;
    lastFocus = d.activeElement;
    prevOverflow = d.body.style.overflow;
    d.body.style.overflow = "hidden";
    layer.hidden = false;
    layer.classList.add("lyg-open");
    if (inputEl) { inputEl.value = ""; inputEl.focus(); }
    if (fromRow) paint();
  }

  function close() {
    if (!layer || layer.hidden) return;
    layer.classList.remove("lyg-open");
    layer.hidden = true;
    d.body.style.overflow = prevOverflow || "";
    if (lastFocus && lastFocus.focus) { try { lastFocus.focus(); } catch (_) {} }
    pendingHref = "";
  }

  function submit() {
    var code = inputEl ? inputEl.value : "";
    if (goEl) { goEl.disabled = true; goEl.textContent = "Checking\u2026"; }
    tryCode(code).then(function (res) {
      if (goEl) goEl.disabled = false;
      if (!res.ok) {
        if (goEl) goEl.textContent = "Unlock downloads";
        if (msgEl) { msgEl.textContent = res.why; msgEl.classList.add("lyg-bad"); }
        return;
      }
      if (msgEl) {
        msgEl.classList.remove("lyg-bad");
        msgEl.textContent = "Unlocked \u2014 " + (res.label ? "code " + res.label : "steward code") +
          (res.until ? ", valid through " + res.until : "") +
          ". Every download button on this page works in this browser now." +
          (pendingHref ? " Close this and press it again, or use the button below." : "");
      }
      if (goEl) goEl.textContent = "Unlocked \u2713";
      if (el("lygGateRelock")) el("lygGateRelock").hidden = false;
      if (pendingHref && el("lygGateContinue")) deleteContinue();
      if (pendingHref) addContinue(pendingHref);
      paint();
    });
  }

  function addContinue(href) {
    var a = d.createElement("a");
    a.id = "lygGateContinue";
    a.className = "lyg-btn lyg-btn-cta";
    a.href = href;
    a.textContent = "Continue to the download \u2192";
    if (goEl && goEl.parentNode) goEl.parentNode.insertBefore(a, goEl);
  }
  function deleteContinue() {
    var n = el("lygGateContinue");
    if (n && n.parentNode) n.parentNode.removeChild(n);
  }

  /* ---- interception: capture phase, so a gated click never starts a download unasked ------ */
  function onClick(e) {
    var a = anchorOf(e.target);
    if (!a || !gatedHref(a.getAttribute("href"))) return;
    if (state().unlocked) return;                 // unlocked: the button behaves normally
    e.preventDefault();
    e.stopPropagation();
    if (e.stopImmediatePropagation) e.stopImmediatePropagation();
    open(a.getAttribute("href"), (a.textContent || "").replace(/\s+/g, " ").trim(), true);
  }

  function wire() {
    if (wired) return;
    wired = true;
    d.addEventListener("click", onClick, true);
    qsa("[data-lyg-gate-open]").forEach(function (n) {
      n.addEventListener("click", function (e) { e.preventDefault(); open("", "", false); });
    });
    qsa("[data-lyg-gate-relock]").forEach(function (n) {
      n.addEventListener("click", function (e) { e.preventDefault(); relock(); });
    });
    paint();
    /* The skill grid is rendered by the page's own script, so new download links can appear
       after load: repaint (debounced) rather than only tagging what exists at boot. */
    if (g.MutationObserver) {
      var t = null;
      new g.MutationObserver(function () {
        if (t) return;
        t = g.setTimeout(function () { t = null; paint(); }, 150);
      }).observe(d.body, { childList: true, subtree: true });
    }
  }

  function relock() { drop(UNLOCK_STORE); paint(); }

  /* The public API — same shape as the portal's and the arcade's, so the pages agree. */
  var API = {
    version: GATE_VERSION,
    storageKey: UNLOCK_STORE,
    patreon: PATREON,
    paypal: PAYPAL,
    unlocked: function () { return state().unlocked; },
    state: state,
    unlock: tryCode,
    relock: relock,
    isGated: isGated,
    wouldBlock: wouldBlock,
    gatedHref: gatedHref,
    open: function () { open("", "", false); },
    close: close,
    paint: paint
  };
  g.LYGODownloadGate = API;

  if (d.readyState === "loading") d.addEventListener("DOMContentLoaded", wire);
  else wire();
})(window, document);
