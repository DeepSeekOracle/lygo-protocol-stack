/** Immutable lattice feed renderer — Haven Star Chart v2 */
(function () {
  const FEED_URLS = [
    'haven_star_chart/haven_star_chart_feed.json',
    'https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/haven_star_chart/haven_star_chart_feed.json',
  ];

  function badge(status, superseded) {
    const s = (status || '').toUpperCase();
    const cls =
      s === 'ACCEPTED' ? 'feed-accept' :
      s === 'REJECTED' ? 'feed-reject' :
      'feed-pending';
    const label = superseded && s === 'PENDING' ? 'PENDING→ACCEPTED' : s;
    return '<span class="feed-badge ' + cls + (superseded ? ' feed-superseded' : '') + '">' + label + '</span>';
  }

  function esc(s) {
    return String(s || '—')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /** Latest status per node_id (by seq). Ledger is append-only history. */
  function latestByNode(rows) {
    const map = Object.create(null);
    rows.forEach(function (e) {
      const id = e.node_id || '';
      if (!id) return;
      const prev = map[id];
      if (!prev || (e.seq || 0) > (prev.seq || 0)) map[id] = e;
    });
    return map;
  }

  function render(feed) {
    const meta = document.getElementById('feedMeta');
    const tbody = document.getElementById('feedBody');
    if (!tbody) return;

    const rows = feed.entries || [];
    const latest = latestByNode(rows);

    let nAccepted = 0, nPendingOnly = 0, nRejected = 0;
    Object.keys(latest).forEach(function (id) {
      const st = (latest[id].status || '').toUpperCase();
      if (st === 'ACCEPTED') nAccepted++;
      else if (st === 'REJECTED') nRejected++;
      else if (st === 'PENDING') nPendingOnly++;
    });

    if (meta) {
      const chain = feed.chain_valid ? '✓ chain valid' : '✗ chain broken';
      meta.innerHTML =
        feed.entry_count + ' ledger events · ' + chain +
        ' · root ' + esc((feed.chain_root || '').slice(0, 12)) + '… · updated ' + esc(feed.updated_utc || '') +
        '<br><span class="feed-muted">Current node state (latest event per node_id): ' +
        '<strong style="color:#2ecc71">' + nAccepted + ' ACCEPTED</strong> · ' +
        '<strong style="color:var(--gold,#ffcc00)">' + nPendingOnly + ' still PENDING</strong> · ' +
        '<strong style="color:#e94560">' + nRejected + ' REJECTED</strong>. ' +
        'PENDING rows below that later show ACCEPTED are historical (submit → steward ingest).</span>';
    }

    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="feed-empty">No agent submissions yet.</td></tr>';
      return;
    }

    tbody.innerHTML = rows
      .map(function (e) {
        const id = e.node_id || '';
        const cur = latest[id];
        const curSt = (cur && cur.status || '').toUpperCase();
        const thisSt = (e.status || '').toUpperCase();
        const superseded =
          thisSt === 'PENDING' &&
          cur &&
          curSt === 'ACCEPTED' &&
          (cur.seq || 0) > (e.seq || 0);

        const who = esc(e.agent_id) + (e.skill_slug ? ' <span class="feed-muted">/' + esc(e.skill_slug) + '</span>' : '');
        const what = '<strong>' + esc(e.node_id) + '</strong> ' + esc(e.node_name);
        const err = (e.errors && e.errors.length)
          ? '<div class="feed-err">' + esc(e.errors.join('; ')) + '</div>'
          : '';
        const note = superseded
          ? '<div class="feed-muted">Historical: gate accepted → pending queue; later ingest_accepted.</div>'
          : '';
        const rowCls = superseded ? ' class="feed-row-superseded"' : '';
        return (
          '<tr' + rowCls + '>' +
          '<td class="feed-time">' + esc((e.event_utc || '').replace('T', ' ').slice(0, 19)) + '</td>' +
          '<td>' + who + '</td>' +
          '<td>' + what + '<br><span class="feed-muted">' + esc(e.kind) + ' · ' + esc(e.event_type) + '</span>' + note + '</td>' +
          '<td>' + badge(e.status, superseded) + '</td>' +
          '<td class="feed-hash">' + esc((e.content_sha256 || '').slice(0, 12)) + '…</td>' +
          '<td>' + err + '</td>' +
          '</tr>'
        );
      })
      .join('');
  }

  async function load() {
    for (const url of FEED_URLS) {
      try {
        const r = await fetch(url, { cache: 'no-store' });
        if (!r.ok) continue;
        render(await r.json());
        return;
      } catch (_) { /* try next */ }
    }
    const tbody = document.getElementById('feedBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="feed-empty">Feed unavailable — rebuild with build_haven_star_chart.py</td></tr>';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
  setInterval(load, 120000);
})();
