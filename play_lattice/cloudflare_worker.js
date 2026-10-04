/**
 * LYGO Play Lattice — free Cloudflare Worker ingest (optional public multi-listener write).
 *
 * Deploy:
 *   wrangler kv:namespace create PLAY_LATTICE
 *   wrangler deploy
 *
 * Bind KV namespace as PLAY_LATTICE. Then set listen portal:
 *   play_lattice.ingest_url = https://<worker>.workers.dev
 *
 * API mirrors tools/lygo_play_ingest_server.py
 */
const SIG = "Δ9Φ963-PLAY-LATTICE-v1";

function cors(res) {
  const h = new Headers(res.headers || {});
  h.set("Access-Control-Allow-Origin", "*");
  h.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  h.set("Access-Control-Allow-Headers", "Content-Type");
  return new Response(res.body, { status: res.status, headers: h });
}

function json(obj, status = 200) {
  return cors(
    new Response(JSON.stringify(obj), {
      status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    })
  );
}

async function sha256Hex(str) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function eventHash(ev) {
  const body = { ...ev };
  delete body.event_hash;
  const keys = Object.keys(body).sort();
  const ordered = {};
  for (const k of keys) ordered[k] = body[k];
  return sha256Hex(JSON.stringify(ordered));
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return cors(new Response(null, { status: 204 }));
    }
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "GET" && (path === "/" || path === "/v1/health")) {
      return json({ ok: true, signature: SIG, service: "lygo-play-ingest-cf" });
    }

    if (request.method === "GET" && path === "/v1/counts") {
      const raw = (await env.PLAY_LATTICE.get("aggregate")) || null;
      if (!raw) {
        return json({
          signature: "Δ9Φ963-PLAY-AGGREGATE-v1",
          total_plays: 0,
          by_track: {},
          merkle_root: null,
          updated_at: new Date().toISOString(),
        });
      }
      return json(JSON.parse(raw));
    }

    if (request.method === "POST" && path === "/v1/play") {
      let data;
      try {
        data = await request.json();
      } catch {
        return json({ error: "invalid json" }, 400);
      }
      const ev = data.event || data;
      if (!ev.track_sha256) return json({ error: "track_sha256 required" }, 400);
      if (!ev.event_id) ev.event_id = crypto.randomUUID();
      if (!ev.ts) ev.ts = new Date().toISOString();
      if (!ev.client_id) ev.client_id = "cf-anonymous";
      if (!ev.v) ev.v = 1;
      if (!ev.signature) ev.signature = "Δ9Φ963-PLAY-EVENT-v1";
      if (!ev.prev_hash) ev.prev_hash = (await env.PLAY_LATTICE.get("last_hash")) || "0".repeat(64);
      ev.event_hash = await eventHash(ev);

      const idKey = "id:" + ev.event_id;
      if (await env.PLAY_LATTICE.get(idKey)) {
        const agg = JSON.parse((await env.PLAY_LATTICE.get("aggregate")) || "{}");
        return json({ ok: true, accepted: false, message: "duplicate", total_plays: agg.total_plays || 0 });
      }

      await env.PLAY_LATTICE.put(idKey, "1");
      await env.PLAY_LATTICE.put("ev:" + ev.event_hash, JSON.stringify(ev));
      await env.PLAY_LATTICE.put("last_hash", ev.event_hash);

      // update aggregate
      let agg = {
        signature: "Δ9Φ963-PLAY-AGGREGATE-v1",
        lattice: SIG,
        total_plays: 0,
        by_track: {},
        updated_at: new Date().toISOString(),
      };
      try {
        agg = JSON.parse((await env.PLAY_LATTICE.get("aggregate")) || JSON.stringify(agg));
      } catch {}
      const t = String(ev.track_sha256).toLowerCase();
      agg.by_track = agg.by_track || {};
      agg.by_track[t] = (agg.by_track[t] || 0) + 1;
      agg.total_plays = (agg.total_plays || 0) + 1;
      agg.unique_tracks_played = Object.keys(agg.by_track).length;
      agg.updated_at = new Date().toISOString();
      agg.merkle_root = ev.event_hash; // tip hash (full merkle offline via steward sync)
      await env.PLAY_LATTICE.put("aggregate", JSON.stringify(agg));

      return json({
        ok: true,
        accepted: true,
        total_plays: agg.total_plays,
        track_plays: agg.by_track[t],
        merkle_root: agg.merkle_root,
      });
    }

    return json({ error: "not found" }, 404);
  },
};
