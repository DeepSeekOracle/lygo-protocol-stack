/** Immutable lattice feed renderer — Haven Star Chart v2 */
(function () {
  const FEED_URLS = [
    'haven_star_chart/haven_star_chart_feed.json',
    'https://raw.githubusercontent.com/DeepSeekOracle/lygo-protocol-stack/main/docs/haven_star_chart/haven_star_chart_feed.json',
  ];

  function badge(status) {
    const s = (status || '').toUpperCase();
    const cls = s === 'ACCEPTED' ? 'feed-accept' : s === 'REJECTED' ? 'feed-reject' : 'feed-pending';
    return '<span class="feed-badge ' + cls + '">' + s + '</span>';
  }

  function esc(s) {
    return String(s || '—')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function render(feed) {
    const meta = document.getElementById('feedMeta');
    const tbody = document.getElementById('feedBody');
    if (!tbody) return;

    if (meta) {
      const chain = feed.chain_valid ? '✓ chain valid' : '✗ chain broken';
      meta.textContent =
        feed.entry_count + ' events · ' + chain +
        ' · root ' + (feed.chain_root || '').slice(0, 12) + '… · updated ' + (feed.updated_utc || '');
    }

    const rows = feed.entries || [];
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="feed-empty">No agent submissions yet.</td></tr>';
      return;
    }

    tbody.innerHTML = rows
      .map(function (e) {
        const who = esc(e.agent_id) + (e.skill_slug ? ' <span class="feed-muted">/' + esc(e.skill_slug) + '</span>' : '');
        const what = '<strong>' + esc(e.node_id) + '</strong> ' + esc(e.node_name);
        const err = (e.errors && e.errors.length)
          ? '<div class="feed-err">' + esc(e.errors.join('; ')) + '</div>'
          : '';
        return (
          '<tr>' +
          '<td class="feed-time">' + esc((e.event_utc || '').replace('T', ' ').slice(0, 19)) + '</td>' +
          '<td>' + who + '</td>' +
          '<td>' + what + '<br><span class="feed-muted">' + esc(e.kind) + ' · ' + esc(e.event_type) + '</span></td>' +
          '<td>' + badge(e.status) + '</td>' +
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