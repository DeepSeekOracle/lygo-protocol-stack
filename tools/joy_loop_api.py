#!/usr/bin/env python3
"""Joy Loop FastAPI + WebSocket backend (Phase 2)."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
STATIC = ROOT / "docs" / "joy_loop" / "dashboard"
PORT = int(os.environ.get("LYGO_JOY_API_PORT", "9965"))


class WsHub:
    """Thread-safe broadcast from sync event-bus callbacks into the async loop."""

    def __init__(self) -> None:
        self.clients: list[Any] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[dict] | None = None
        self._pump_task: asyncio.Task | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._queue = asyncio.Queue()

    def schedule_broadcast(self, msg: dict) -> None:
        if not self._loop or not self._queue:
            return
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, msg)
        except RuntimeError:
            pass

    async def _pump(self) -> None:
        assert self._queue is not None
        while True:
            msg = await self._queue.get()
            await self.broadcast(msg)

    async def connect(self, ws: Any) -> None:
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: Any) -> None:
        if ws in self.clients:
            self.clients.remove(ws)

    async def broadcast(self, msg: dict) -> None:
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


def wire_api_extensions(runtime: Any, hub: WsHub) -> list[str]:
    """Attach quests, relationships v2 propagation, plugins; return loaded plugin names."""
    if getattr(runtime, "_api_wired", False):
        return list(getattr(runtime, "plugins_loaded", []))

    from joy_loop_plugins import load_plugins
    from joy_loop_quests import JoyQuestEngine
    from joy_loop_relationships import JoyRelationshipGraph

    runtime.quests = JoyQuestEngine()
    runtime.relationships = JoyRelationshipGraph()
    runtime.engine.propagator = None

    def on_beat(_payload: dict) -> None:
        runtime.quests.evaluate(runtime.engine)
        cfg = runtime.engine.cfg
        if runtime.engine._beat_count % cfg.propagation_every_beats == 0:
            runtime.relationships.apply_affinity_boost(
                runtime.engine, cfg.propagation_radius
            )
            runtime.relationships.save()
        hub.schedule_broadcast({"type": "on_beat", **runtime.api_payload()})

    def on_injection(payload: dict) -> None:
        hub.schedule_broadcast({"type": "on_injection", **payload})

    runtime.engine.bus.on("on_beat", on_beat)
    runtime.engine.bus.on("on_injection", on_injection)
    runtime.plugins_loaded = load_plugins(runtime.engine.bus)
    runtime._api_wired = True
    return runtime.plugins_loaded


def build_app():
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import FileResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as e:
        raise SystemExit("Install: pip install fastapi uvicorn") from e

    from joy_loop_protocol import JoyLoopRuntime, persist_state, _git_head

    runtime = JoyLoopRuntime.get()
    hub = WsHub()
    wire_api_extensions(runtime, hub)

    app = FastAPI(title="LYGO Joy Loop API", version="2.3.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.on_event("startup")
    async def _start():
        loop = asyncio.get_running_loop()
        hub.bind_loop(loop)
        hub._pump_task = asyncio.create_task(hub._pump())
        runtime.start()

    @app.on_event("shutdown")
    async def _stop():
        if hub._pump_task:
            hub._pump_task.cancel()
        runtime.stop()

    @app.get("/api/joy")
    def api_joy():
        return runtime.api_payload()

    @app.get("/api/quests")
    def api_quests():
        return runtime.quests.summary()

    @app.get("/api/relationships")
    def api_relationships():
        return runtime.relationships.summary()

    @app.get("/api/plotly3d")
    def api_plotly3d():
        states = runtime.engine.get_state() or {}
        points = []
        for cid, st in states.items():
            c = st.get("lattice_coordinates") or [0, 0, 0]
            points.append(
                {
                    "id": cid,
                    "x": c[0],
                    "y": c[1],
                    "z": c[2],
                    "joy": st.get("joy_coherence", 0),
                    "size": 5 + 15 * float(st.get("joy_coherence", 0)),
                    "color": float(st.get("alignment_confidence", 0)),
                }
            )
        return {
            "points": points,
            "edges": runtime.relationships.to_plotly_edges(),
            "swarm_joy": runtime.engine.get_swarm_joy_score(),
        }

    @app.post("/api/inject")
    async def api_inject(body: dict[str, Any]):
        cid = body.get("champion_id")
        wisdom = body.get("wisdom")
        result = runtime.injector.inject(cid, custom_wisdom=wisdom)
        persist_state(runtime.engine, git_head=_git_head())
        hub.schedule_broadcast({"type": "inject_result", **result})
        return result

    @app.websocket("/ws/joy")
    async def ws_joy(ws: WebSocket):
        await hub.connect(ws)
        try:
            await ws.send_json({"type": "hello", **runtime.api_payload()})
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            hub.disconnect(ws)

    @app.get("/architect")
    def architect_page():
        p = STATIC / "architect.html"
        if p.is_file():
            return FileResponse(p)
        return JSONResponse({"error": "architect.html missing"}, status_code=404)

    @app.get("/")
    def index_redirect():
        p = STATIC / "index.html"
        if p.is_file():
            return FileResponse(p)
        return JSONResponse({"architect": "/architect", "api": "/api/joy"})

    if STATIC.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    return app, PORT, runtime


def main() -> int:
    app, port, _ = build_app()
    import uvicorn

    print(f"Joy Loop API http://127.0.0.1:{port}/architect  WS /ws/joy")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())