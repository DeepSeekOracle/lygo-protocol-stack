/* Mini listen-portal radio. Toggle hides the panel; audio element stays in the DOM and keeps playing. Mute is volume, not pause. */
(() => {
  const HUB = "https://asiancoastline.com/listen.html";
  const PLAYLISTS = [
    "./radio.json",
    "https://asiancoastline.com/data/public_stream_playlist.json",
    "https://deepseekoracle.github.io/Excavationpro/data/public_stream_playlist.json"
  ];
  const $ = (id) => document.getElementById(id);
  const el = () => $("radioEl");

  const st = {
    tracks: [],
    i: 0,
    playing: false,
    muted: false,
    view: true,
    vol: 0.55,
    bag: []
  };

  function normTrack(t) {
    const url = t.stream_url || t.url;
    const title = t.title || t.name || "Untitled";
    if (!url) return null;
    return { title, url };
  }

  function ingest(data) {
    const raw = Array.isArray(data) ? data : (data.tracks || []);
    const out = [];
    for (const t of raw) {
      const n = normTrack(t);
      if (n) out.push(n);
    }
    if (out.length) st.tracks = out;
  }

  async function loadPlaylists() {
    try {
      const local = await fetch("./radio.json", { cache: "no-cache" }).then((r) => r.json());
      ingest(local);
    } catch (_) {}
    for (const url of PLAYLISTS.slice(1)) {
      try {
        const data = await fetch(url, { mode: "cors" }).then((r) => {
          if (!r.ok) throw new Error(String(r.status));
          return r.json();
        });
        ingest(data);
        if (st.tracks.length > 40) break;
      } catch (_) { /* CORS or offline — local radio.json still works */ }
    }
    refill();
  }

  function refill() {
    st.bag = st.tracks.map((_, i) => i);
    for (let i = st.bag.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [st.bag[i], st.bag[j]] = [st.bag[j], st.bag[i]];
    }
  }

  function paint() {
    const title = $("radioTitle");
    const play = $("radioPlay");
    const mute = $("radioMute");
    const view = $("radioView");
    const dock = $("radioDock");
    const t = st.tracks[st.i];
    const line = t
      ? ((st.playing ? "Now playing · " : "Paused · ") + t.title)
      : "Now playing · idle";
    if (title) {
      title.textContent = t
        ? (st.playing ? "▶ " : "❚❚ ") + t.title
        : "Loading listen portal…";
    }
    const now = $("radioNow");
    if (now) now.textContent = line;
    const side = $("nowPlaying");
    if (side) side.textContent = line;
    if (play) play.textContent = st.playing ? "Pause" : "Play";
    if (mute) mute.textContent = st.muted ? "Unmute" : "Mute";
    if (view) view.textContent = st.view ? "Hide" : "Radio";
    if (dock) dock.classList.toggle("collapsed", !st.view);
    const a = el();
    if (a) {
      a.muted = st.muted;
      a.volume = st.vol;
    }
  }

  function loadIndex(i) {
    if (!st.tracks.length) return;
    st.i = ((i % st.tracks.length) + st.tracks.length) % st.tracks.length;
    const a = el();
    const t = st.tracks[st.i];
    if (!a || !t) return;
    a.src = t.url;
    a.volume = st.vol;
    a.muted = st.muted;
    paint();
  }

  function next() {
    if (!st.bag.length) refill();
    const i = st.bag.pop();
    loadIndex(i == null ? Math.floor(Math.random() * st.tracks.length) : i);
    if (st.playing) el().play().catch(() => {});
  }

  function play() {
    if (!st.tracks.length) return;
    const a = el();
    if (!a.src) next();
    a.play().then(() => { st.playing = true; paint(); }).catch(() => {
      next();
    });
  }

  function pauseKeep() {
    el().pause();
    st.playing = false;
    paint();
  }

  function bootRadio() {
    loadPlaylists().then(paint);
    const a = el();
    a.addEventListener("ended", () => { st.playing = true; next(); });
    a.addEventListener("error", () => { if (st.playing) next(); });
    const playBtn = $("radioPlay");
    const nextBtn = $("radioNext");
    const muteBtn = $("radioMute");
    const viewBtn = $("radioView");
    const vol = $("radioVol");
    if (playBtn) playBtn.onclick = () => { st.playing ? pauseKeep() : play(); };
    if (nextBtn) nextBtn.onclick = () => { st.playing = true; next(); };
    if (muteBtn) muteBtn.onclick = () => {
      st.muted = !st.muted;
      el().muted = st.muted;
      paint();
    };
    if (viewBtn) viewBtn.onclick = () => {
      st.view = !st.view;
      paint();
    };
    if (vol) vol.oninput = (e) => {
      st.vol = Number(e.target.value) / 100;
      el().volume = st.vol;
      if (st.vol > 0 && st.muted) {
        st.muted = false;
        el().muted = false;
      }
      paint();
    };
    paint();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bootRadio);
  else bootRadio();
})();
