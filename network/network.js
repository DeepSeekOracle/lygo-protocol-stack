(function () {
  "use strict";
  var PULSE = [
    "../agent-agora/api/pulse.json",
    "https://deepseekoracle.github.io/lygo-protocol-stack/agent-agora/api/pulse.json"
  ];
  var ANCHORS = [
    "../network_builder/IMMUTABLE_ANCHORS.json",
    "https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/network_builder/IMMUTABLE_ANCHORS.json"
  ];

  function set(id, text, cls) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.className = cls || "";
  }

  function getJson(urls) {
    return (function next(i) {
      if (i >= urls.length) return Promise.reject(new Error("all failed"));
      return fetch(urls[i], { credentials: "omit" }).then(function (r) {
        if (!r.ok) throw new Error("http " + r.status);
        return r.json();
      }).catch(function () { return next(i + 1); });
    })(0);
  }

  getJson(PULSE).then(function (p) {
    set("p-nodes", String(p.chart_nodes != null ? p.chart_nodes : "—"), "ok");
    set("p-feed", String(p.feed_entries != null ? p.feed_entries : "—"), "ok");
    set("p-marks", String((p.marks && p.marks.count) != null ? p.marks.count : "—"));
    set("p-write", p.writes === false ? "GET only" : String(p.writes), p.writes === false ? "ok" : "bad");
    set("p-status", "LIVE pulse · RESOURCE", "ok");
  }).catch(function () {
    set("p-status", "Pulse blocked in this browser — open JSON below", "bad");
  });

  getJson(ANCHORS).then(function (a) {
    var n = a.category_count || (a.categories && a.categories.length) || (a.anchors && a.anchors.length);
    set("p-anchors", n != null ? String(n) : (a.version || "ok"), "ok");
  }).catch(function () {
    set("p-anchors", "open ledger", "");
  });
})();
