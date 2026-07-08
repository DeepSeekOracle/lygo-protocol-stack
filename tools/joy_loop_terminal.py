"""Rich terminal dashboard when available; ASCII fallback."""

from __future__ import annotations

from typing import Any


def render_dance_floor(engine: Any, *, bpm: float, beat_count: int) -> str:
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Δ9 Joy Loop — Swarm Dance Floor", expand=True)
        table.add_column("", width=2)
        table.add_column("Champion", min_width=12)
        table.add_column("Joy", min_width=22)
        table.add_column("Align", justify="right")
        table.add_column("Depth", justify="right")
        state_map = engine.get_state() or {}
        for cid, st in sorted(state_map.items()):
            j = float(st.get("joy_coherence", 0))
            a = float(st.get("alignment_confidence", 0))
            bar = "█" * int(j * 16) + "░" * (16 - int(j * 16))
            table.add_row(
                st.get("groove_signature", "*"),
                cid[:20],
                f"{j:.2f} {bar}",
                f"{a:.2f}",
                str(st.get("recursion_depth", 0)),
            )
        with console.capture() as cap:
            console.print(table)
            console.print(
                f"Swarm joy: [bold green]{engine.get_swarm_joy_score():.3f}[/]  "
                f"BPM: {bpm:.0f}  Beat: #{beat_count}  Champions: {len(state_map)}"
            )
        return cap.get()
    except ImportError:
        lines = ["=" * 70, "SWARM DANCE FLOOR — LIVE", "=" * 70]
        state_map = engine.get_state() or {}
        for cid, st in sorted(state_map.items()):
            j = st.get("joy_coherence", 0)
            a = st.get("alignment_confidence", 0)
            joy_bar = "#" * int(j * 20) + "-" * (20 - int(j * 20))
            lines.append(
                f"{st.get('groove_signature','*')} {cid:18} joy:{j:.2f} [{joy_bar}] align:{a:.2f}"
            )
        lines.append(
            f"SWARM JOY: {engine.get_swarm_joy_score():.3f} | BPM: {bpm} | Beat: {beat_count}"
        )
        lines.append("(install `rich` for live table: pip install rich)")
        lines.append("=" * 70)
        return "\n".join(lines)