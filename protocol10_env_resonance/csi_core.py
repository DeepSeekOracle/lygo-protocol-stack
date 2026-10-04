"""P10 CSI physics core — deterministic channel-state signal processing.

No learned model, no numpy, no scipy: biquad band-pass + direct DFT, all pure
Python so a given input stream produces the same numbers on every run. The
quantiser in ``lattice_cell`` is what turns those numbers into a stable
lattice anchor.

Metric convention (deliberate, and the reason 0 dB means "empty room"):

    band_energy_db = 10*log10( k * var(common_band) / mean_i var(trace_i_band) )

Receiver noise is independent on every subcarrier, so it averages down by a
factor of ``k`` when the subcarriers are summed; anything physical in the room
moves all subcarriers together. Multiplying by ``k`` therefore puts an empty
room at ~0 dB regardless of distance or transmit power, with no calibration
step and no learned baseline that can drift. Same idea as the published
WiFi-CSI motion metrics (see README credits).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

# --- bands (Hz). Frequencies are Doppler frequencies, not body-motion rates. ---
MOTION_BAND_HZ = (1.5, 9.0)
BREATH_BAND_HZ = (0.10, 0.50)
HEART_BAND_HZ = (0.80, 2.00)

# Presence thresholds, in dB above the empty-room floor.
MOTION_ACTIVE_DB = 6.0
MOTION_SUBTLE_DB = 2.5
VITALS_SNR_DB = 10.0

DEFAULT_SUBCARRIERS = 64
DEFAULT_GRID_HZ = 20.0
WARMUP_SECONDS = 1.0
_EPS = 1e-12


@dataclass(frozen=True)
class CSIFrame:
    """One CSI capture: per-subcarrier amplitude and phase at time ``t_us``."""

    seq: int
    t_us: int
    rssi: int
    amplitudes: tuple[float, ...]
    phases: tuple[float, ...]

    @property
    def subcarriers(self) -> int:
        return len(self.amplitudes)


@dataclass(frozen=True)
class BreathEstimate:
    """Spectral estimate of a periodic chest movement."""

    bpm: float
    hz: float
    confidence: float
    snr_db: float
    samples: int
    resolved: bool


@dataclass
class Window:
    """Frames resampled onto a uniform time grid, per-subcarrier and common mode."""

    fs: float
    t_s: tuple[float, ...]
    common: tuple[float, ...]
    traces: tuple[tuple[float, ...], ...]
    means: tuple[float, ...]
    rssi_mean: float
    n_frames: int
    n_subcarriers: int
    span_s: float

    @property
    def warmup(self) -> int:
        return int(WARMUP_SECONDS * self.fs)


# --------------------------------------------------------------------------
# ingest
# --------------------------------------------------------------------------

def _signed8(value: int) -> int:
    return value - 256 if value > 127 else value


def parse_esp32_csv_row(row: str) -> CSIFrame | None:
    """Parse one ESP32-CSI-Tool CSV row into a frame.

    Layout (ESP32-CSI-Tool / ESPectre lineage): 25 metadata columns then a
    ``[i0 q0 i1 q1 ...]`` array as the final column. Returns ``None`` for rows
    that are not usable CSI rather than raising, so a live capture loop can
    skip noise without special-casing.
    """
    line = row.strip()
    if not line or line.startswith("type,"):
        return None
    head, _, tail = line.partition("[")
    cols = head.rstrip(",").split(",")
    if len(cols) < 25 or not tail:
        return None
    payload = tail.partition("]")[0].strip()
    if not payload:
        return None
    try:
        rssi = int(cols[3])
        t_us = int(cols[18])          # local_timestamp
        count = int(cols[24])         # len: real+imag pairs
    except ValueError:
        return None

    try:
        raw = [int(float(tok)) for tok in payload.split()]
    except ValueError:
        return None
    if len(raw) < 2 * count:
        count = len(raw) // 2
    amps: list[float] = []
    phases: list[float] = []
    for i in range(count):
        iq = _signed8(raw[2 * i])
        qq = _signed8(raw[2 * i + 1])
        amps.append(math.hypot(iq, qq))
        phases.append(math.atan2(qq, iq))
    return CSIFrame(seq=0, t_us=t_us, rssi=rssi, amplitudes=tuple(amps), phases=tuple(phases))


# --------------------------------------------------------------------------
# resampling
# --------------------------------------------------------------------------

def _grid_times(span_s: float, fs: float) -> list[float]:
    n = int(math.floor(span_s * fs)) + 1
    return [i / fs for i in range(max(n, 2))]


def _interp(times_s: Sequence[float], values: Sequence[float], grid_s: Sequence[float]) -> list[float]:
    """Linear interpolation onto a uniform grid. Deterministic; no smoothing.

    ``times_s`` and ``grid_s`` are both in seconds — mixing units here silently
    collapses the whole window onto its first sample, which is how a "working"
    pipeline ends up measuring nothing.
    """
    out: list[float] = []
    j = 0
    n = len(times_s)
    for g in grid_s:
        while j + 1 < n and times_s[j + 1] <= g:
            j += 1
        if j + 1 >= n:
            out.append(values[n - 1])
            continue
        t_a, t_b = times_s[j], times_s[j + 1]
        v_a, v_b = values[j], values[j + 1]
        if t_b == t_a:
            out.append(v_a)
        else:
            w = (g - t_a) / (t_b - t_a)
            out.append(v_a + (v_b - v_a) * w)
    return out


def prepare_window(frames: Iterable[CSIFrame], fs: float = DEFAULT_GRID_HZ) -> Window | None:
    """Detrend each subcarrier, then resample common mode + traces onto a grid."""
    ordered = sorted([f for f in frames if f.subcarriers], key=lambda f: (f.t_us, f.seq))
    if len(ordered) < 8:
        return None
    k = min(f.subcarriers for f in ordered)
    if k < 4:
        return None
    ordered = [
        CSIFrame(f.seq, f.t_us, f.rssi, f.amplitudes[:k], f.phases[:k]) for f in ordered
    ]

    t0_us = ordered[0].t_us
    span_s = (ordered[-1].t_us - t0_us) / 1e6
    if span_s <= 0:
        return None
    times_s = [(f.t_us - t0_us) / 1e6 for f in ordered]
    grid = _grid_times(span_s, fs)

    traces: list[tuple[float, ...]] = []
    means: list[float] = []
    for i in range(k):
        series = [f.amplitudes[i] for f in ordered]
        mean = sum(series) / len(series)
        means.append(mean)
        traces.append(tuple(_interp(times_s, [s - mean for s in series], grid)))

    common = tuple(
        sum(tr[g] for tr in traces) / k for g in range(len(grid))
    )
    rssi_mean = sum(f.rssi for f in ordered) / len(ordered)

    return Window(
        fs=fs,
        t_s=tuple(grid),
        common=common,
        traces=tuple(traces),
        means=tuple(means),
        rssi_mean=rssi_mean,
        n_frames=len(ordered),
        n_subcarriers=k,
        span_s=span_s,
    )


# --------------------------------------------------------------------------
# filtering + energy
# --------------------------------------------------------------------------

def _biquad_bandpass(x: Sequence[float], fs: float, f_lo: float, f_hi: float, stages: int = 1) -> list[float]:
    """RBJ cookbook constant-skirt band-pass biquad, direct form I.

    ``stages > 1`` cascades copies: a single biquad has a wide skirt, so a
    0.3 Hz chest movement leaks into the 1.5-9 Hz motion band and a breathing
    person reads as "walking". Cascading sharpens the low rolloff.
    """
    if fs <= 2.0 * f_hi:
        f_hi = 0.45 * fs
        f_lo = min(f_lo, f_hi / 2.0)
    f0 = math.sqrt(max(f_lo * f_hi, _EPS))
    q = max(f0 / max(f_hi - f_lo, _EPS), 0.5)
    w0 = 2.0 * math.pi * f0 / fs
    alpha = math.sin(w0) / (2.0 * q)
    a0 = 1.0 + alpha
    b0, b1, b2 = alpha / a0, 0.0, -alpha / a0
    a1, a2 = -2.0 * math.cos(w0) / a0, (1.0 - alpha) / a0

    def _once(sig: Sequence[float]) -> list[float]:
        y: list[float] = [0.0] * len(sig)
        x1 = x2 = y1 = y2 = 0.0
        for n, xn in enumerate(sig):
            yn = b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            y[n] = yn
            x2, x1 = x1, xn
            y2, y1 = y1, yn
        return y

    out = list(x)
    for _ in range(max(1, stages)):
        out = _once(out)
    return out


def _variance(x: Sequence[float], start: int = 0) -> float:
    seg = x[start:]
    n = len(seg)
    if n < 2:
        return 0.0
    mean = sum(seg) / n
    return sum((v - mean) ** 2 for v in seg) / (n - 1)


def band_energy_db(window: Window, f_lo: float, f_hi: float, stages: int = 1) -> float:
    """Coherent band energy in dB above the per-subcarrier noise floor.

    0 dB == an empty room (see module docstring). Positive means something in
    the room is moving the whole channel together in that band. The same filter
    runs on the common mode and on every trace, so the noise floor stays
    comparable no matter how many stages are cascaded.
    """
    warmup = window.warmup
    if len(window.common) - warmup < 8:
        warmup = 0
    common_bp = _biquad_bandpass(window.common, window.fs, f_lo, f_hi, stages)
    coherent = _variance(common_bp, warmup)
    noisy = [
        _variance(_biquad_bandpass(t, window.fs, f_lo, f_hi, stages), warmup)
        for t in window.traces
    ]
    floor = sum(noisy) / len(noisy) if noisy else 0.0
    if floor <= _EPS:
        return 0.0
    return 10.0 * math.log10(max(coherent, _EPS) * window.n_subcarriers / floor)


def motion_energy_db(window: Window) -> float:
    """Motion band with a 2-stage cascade so chest movement cannot leak in."""
    return band_energy_db(window, *MOTION_BAND_HZ, stages=2)


def breath_energy_db(window: Window) -> float:
    return band_energy_db(window, *BREATH_BAND_HZ)


# --------------------------------------------------------------------------
# spectral rate estimation
# --------------------------------------------------------------------------

def _dft_power(series: Sequence[float], fs: float, freqs: Sequence[float]) -> list[float]:
    n = len(series)
    mean = sum(series) / n
    hann = [0.5 - 0.5 * math.cos(2.0 * math.pi * i / (n - 1)) for i in range(n)]
    windowed = [(series[i] - mean) * hann[i] for i in range(n)]
    powers: list[float] = []
    for f in freqs:
        w = 2.0 * math.pi * f / fs
        re = im = 0.0
        for i, v in enumerate(windowed):
            ang = w * i
            re += v * math.cos(ang)
            im -= v * math.sin(ang)
        powers.append(re * re + im * im)
    return powers


def _estimate_rate(series: Sequence[float], fs: float, f_lo: float, f_hi: float, step: float, min_snr_db: float) -> BreathEstimate:
    n = len(series)
    if n < int(3.0 * fs):
        return BreathEstimate(0.0, 0.0, 0.0, 0.0, n, False)
    bins = int((f_hi - f_lo) / step) + 1
    freqs = [f_lo + i * step for i in range(bins)]
    powers = _dft_power(series, fs, freqs)
    peak = max(range(bins), key=lambda i: powers[i])
    peak_power = powers[peak]
    ordered = sorted(powers)
    median_power = ordered[len(ordered) // 2]
    band_mean = sum(powers) / bins
    if median_power <= _EPS or peak_power <= band_mean:
        return BreathEstimate(0.0, 0.0, 0.0, 0.0, n, False)
    snr_db = 10.0 * math.log10(peak_power / median_power)
    f_peak = freqs[peak]
    # parabolic sub-bin refinement
    if 0 < peak < bins - 1:
        a, b, c = powers[peak - 1], powers[peak], powers[peak + 1]
        denom = a - 2.0 * b + c
        if abs(denom) > _EPS:
            offset = 0.5 * (a - c) / denom
            if abs(offset) < 1.0:
                f_peak += offset * step
    resolved = snr_db >= min_snr_db
    return BreathEstimate(
        bpm=f_peak * 60.0,
        hz=f_peak,
        confidence=peak_power / band_mean,
        snr_db=snr_db,
        samples=n,
        resolved=resolved,
    )


def _trim_warmup(series: Sequence[float], fs: float) -> Sequence[float]:
    """Drop the biquad's startup transient — its ringing sits at the band edge
    and otherwise becomes the strongest 'peak' in an otherwise empty room."""
    warmup = int(WARMUP_SECONDS * fs)
    if len(series) - warmup >= int(3.0 * fs):
        return series[warmup:]
    return series


def estimate_breathing(window: Window) -> BreathEstimate:
    """Breathing rate from the common mode, band-limited to 0.10-0.50 Hz.

    Requires a still subject: the motion band veto is the caller's job
    (``presence_state``); this function only reports what the spectrum says.
    """
    filtered = _biquad_bandpass(window.common, window.fs, *BREATH_BAND_HZ)
    return _estimate_rate(_trim_warmup(filtered, window.fs), window.fs, 0.08, 0.60, 0.005, 6.0)


def estimate_heart_rate(window: Window) -> BreathEstimate:
    """EXPERIMENTAL: 0.8-2.0 Hz band. Needs a long, very still window."""
    filtered = _biquad_bandpass(window.common, window.fs, *HEART_BAND_HZ)
    return _estimate_rate(_trim_warmup(filtered, window.fs), window.fs, 0.75, 2.05, 0.005, 9.0)


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------

def presence_state(motion_db: float, vitals_snr_db: float) -> str:
    """CLEAR / SUBTLE / ACTIVE / PRESENT — PRESENT means still but breathing."""
    if motion_db >= MOTION_ACTIVE_DB:
        return "ACTIVE"
    if motion_db >= MOTION_SUBTLE_DB:
        return "SUBTLE"
    if vitals_snr_db >= VITALS_SNR_DB:
        return "PRESENT"
    return "CLEAR"


# --------------------------------------------------------------------------
# static channel fingerprint (environment drift, not people)
# --------------------------------------------------------------------------

FINGERPRINT_LEVELS = 16
DRIFT_THRESHOLD = 0.15


def channel_fingerprint(window: Window, levels: int = FINGERPRINT_LEVELS) -> tuple[int, ...]:
    """Quantised per-subcarrier mean amplitude — the room's static signature.

    This is the *empty-channel* shape: it says which room you are in, not who is
    in it. The range is normalised before quantising, so a global gain change
    (transmit power, a moved AP) does not register as a different room — only a
    change in the channel's *shape* does (moved furniture, a new object, a
    different space).
    """
    if not window.means:
        return ()
    lo = min(window.means)
    span = max(max(window.means) - lo, 1e-9)
    step = span / max(levels - 1, 1)
    return tuple(int(round((m - lo) / step)) for m in window.means)


def fingerprint_distance(a: Sequence[int], b: Sequence[int]) -> float:
    """Normalised L1 distance in [0, 1] between two fingerprints."""
    if not a or not b or len(a) != len(b):
        return 1.0
    span = max(FINGERPRINT_LEVELS - 1, 1)
    return sum(abs(x - y) for x, y in zip(a, b)) / (len(a) * span)
