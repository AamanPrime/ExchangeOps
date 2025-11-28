"""
ExchangeOPS Simulator – Python rewrite of the Go simulator.

Endpoints (same contract as the Go version):
  GET  /health
  GET  /exchanges
  GET  /exchanges/<name>
  POST /exchanges/<name>/restart
  POST /exchanges/<name>/inject-failure
  GET  /exchanges/<name>/orderbook
  WS   /ws/exchanges           (pushes all states every second)

Run:
  python simulator.py
  # or with gunicorn + gevent-websocket:
  # gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 simulator:app
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import signal
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from flask import Flask, jsonify, request, Response
from flask_sock import Sock

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Domain models
# ─────────────────────────────────────────────
STATUS_UP       = "UP"
STATUS_DEGRADED = "DEGRADED"
STATUS_DOWN     = "DOWN"


@dataclass
class Level:
    price: float
    size: int


@dataclass
class OrderBook:
    bids: List[dict]
    asks: List[dict]


@dataclass
class ExchangeState:
    name: str
    failure_rate: float
    status: str = STATUS_UP
    last_heartbeat: str = field(default_factory=lambda: _now_iso())
    consecutive_misses: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "consecutive_misses": self.consecutive_misses,
            "failure_rate": self.failure_rate,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────
# Exchange Manager
# ─────────────────────────────────────────────
class ExchangeManager:
    def __init__(self) -> None:
        self._states: Dict[str, ExchangeState] = {}
        self._chaos_drops: Dict[str, int] = {}
        self._lock = threading.Lock()

    # ── lifecycle ──────────────────────────────
    def add_exchange(self, name: str, failure_rate: float) -> None:
        with self._lock:
            self._states[name] = ExchangeState(name=name, failure_rate=failure_rate)
            self._chaos_drops[name] = 0

    def start_simulation(self, name: str) -> None:
        """Blocking loop – run each exchange in its own daemon thread."""
        while True:
            time.sleep(2)
            self._simulate_tick(name)

    # ── tick logic ─────────────────────────────
    def _simulate_tick(self, name: str) -> None:
        with self._lock:
            state = self._states.get(name)
            if state is None:
                return

            chaos = self._chaos_drops.get(name, 0)
            drop = False

            if chaos > 0:
                drop = True
                self._chaos_drops[name] = chaos - 1
            elif random.random() < state.failure_rate:
                drop = True

            if drop:
                state.consecutive_misses += 1
                if state.consecutive_misses >= 3:
                    state.status = STATUS_DOWN
                elif state.consecutive_misses >= 1:
                    state.status = STATUS_DEGRADED
            else:
                state.status = STATUS_UP
                state.consecutive_misses = 0
                state.last_heartbeat = _now_iso()

    # ── read helpers ───────────────────────────
    def get_all_states(self) -> List[dict]:
        with self._lock:
            return [s.to_dict() for s in self._states.values()]

    def get_state(self, name: str) -> Optional[dict]:
        with self._lock:
            s = self._states.get(name)
            return s.to_dict() if s else None

    # ── mutations ──────────────────────────────
    def restart(self, name: str) -> bool:
        with self._lock:
            state = self._states.get(name)
            if state is None:
                return False
            state.status = STATUS_UP
            state.consecutive_misses = 0
            state.last_heartbeat = _now_iso()
            self._chaos_drops[name] = 0
            return True

    def inject_failure(self, name: str, drops: int = 3) -> bool:
        with self._lock:
            if name not in self._states:
                return False
            self._chaos_drops[name] = drops
            return True

    def generate_order_book(self, name: str) -> dict:
        base_price = float(len(name) * 100)
        bids = [{"price": base_price - (i + 1) * 0.5, "size": random.randint(1, 100)} for i in range(5)]
        asks = [{"price": base_price + (i + 1) * 0.5, "size": random.randint(1, 100)} for i in range(5)]
        return {"bids": bids, "asks": asks}


# ─────────────────────────────────────────────
# Config loader
# ─────────────────────────────────────────────
def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# Flask app + routes
# ─────────────────────────────────────────────
app  = Flask(__name__)
sock = Sock(app)

manager: ExchangeManager = ExchangeManager()


def _not_found(name: str) -> Response:
    return jsonify({"error": f"exchange '{name}' not found"}), 404


@app.get("/health")
def handle_health():
    return "OK", 200


@app.get("/exchanges")
def handle_list_exchanges():
    return jsonify(manager.get_all_states())


@app.get("/exchanges/<name>")
def handle_get_exchange(name: str):
    state = manager.get_state(name)
    if state is None:
        return _not_found(name)
    return jsonify(state)


@app.post("/exchanges/<name>/restart")
def handle_restart_exchange(name: str):
    if not manager.restart(name):
        return _not_found(name)
    return "Restarted", 200


@app.post("/exchanges/<name>/inject-failure")
def handle_inject_failure(name: str):
    if not manager.inject_failure(name, drops=3):
        return _not_found(name)
    return "Failure injected (3 drops)", 200


@app.get("/exchanges/<name>/orderbook")
def handle_get_order_book(name: str):
    if manager.get_state(name) is None:
        return _not_found(name)
    return jsonify(manager.generate_order_book(name))


@sock.route("/ws/exchanges")
def handle_ws_exchanges(ws):
    """Push all exchange states to the client every second."""
    log.info("WebSocket client connected")
    try:
        while True:
            states = manager.get_all_states()
            ws.send(json.dumps(states))
            time.sleep(1)
    except Exception as exc:
        log.info("WebSocket client disconnected: %s", exc)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def _graceful_shutdown(signum, frame):
    log.info("Shutting down simulator...")
    sys.exit(0)


def main():
    config_path = os.path.join(os.path.dirname(__file__), "exchanges.json")
    cfg = load_config(config_path)

    for ex in cfg["exchanges"]:
        manager.add_exchange(ex["name"], ex["failure_rate"])
        t = threading.Thread(
            target=manager.start_simulation,
            args=(ex["name"],),
            daemon=True,
            name=f"sim-{ex['name']}",
        )
        t.start()
        log.info("Started simulation thread for %s", ex["name"])

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT,  _graceful_shutdown)

    port = int(os.environ.get("SIMULATOR_PORT", 8088))
    log.info("Simulator running on :%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
