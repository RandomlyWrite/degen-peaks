"""
mini_app.py

Mini App backend for Fear and Loathing in Degen Vegas.

Runs in the SAME process as the Telegram bot so it can share the database
and in-memory state (_responded, sessions, etc.) with zero IPC.

Routes:
  GET  /peak?c=<challenge>&peak_id=<id>   → serves the HTML Mini App
  POST /api/peak/answer                   → receives result, updates GoR/Gonzo
  POST /api/peak/challenge                → returns per-player secret content

Security note:
  initData validation is the only thing standing between you and forged results.
  Never trust the client about who they are or whether they succeeded.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web

from db.database import get_player

# ───────────────────────────────────────────────────────────────────
# Peak Registry
# ───────────────────────────────────────────────────────────────────
# Single source of truth for every Peak.
# Add new challenges here.

PEAK_REGISTRY = {
    "bat_swarm": {
        "html": "batswarm.html",
        "resolver": "bat_swarm",
        "has_payload": False,
        "gor_loss": 16,
        "gonzo_gain": 12,
        "timeout": 28,
    },
    "attorneys_advice": {
        "html": "attorney.html",
        "resolver": "attorneys_advice",
        "has_payload": True,
        "gor_loss": 15,
        "gonzo_gain": 10,
        "timeout": 25,
    },
    "lizard_loyalty": {
        "html": "lizard.html",
        "resolver": "lizard_loyalty",
        "has_payload": True,
        "gor_loss": 16,
        "gonzo_gain": 12,
        "timeout": 22,
    },
    "mile_marker_zero": {
        "html": "milemarker.html",
        "resolver": "mile_marker_zero",
        "has_payload": False,
        "gor_loss": 16,
        "gonzo_gain": 12,
        "timeout": 30,
    },
    "stagger": {
        "html": "stagger.html",
        "resolver": "stagger",
        "has_payload": False,
        "gor_loss": 15,
        "gonzo_gain": 11,
        "timeout": 26,
    },
    "hitchhiker": {
        "html": "hitchhiker.html",
        "resolver": "hitchhiker",
        "has_payload": False,
        "gor_loss": 15,
        "gonzo_gain": 11,
        "timeout": 24,
    },
    "bandit": {
        "html": "bandit.html",
        "resolver": "bandit",
        "has_payload": False,
        "gor_loss": 14,
        "gonzo_gain": 10,
        "timeout": 22,
    },
    "trunk": {
        "html": "trunk.html",
        "resolver": "trunk",
        "has_payload": False,
        "gor_loss": 15,
        "gonzo_gain": 11,
        "timeout": 25,
    },
    "shark": {
        "html": "shark.html",
        "resolver": "shark",
        "has_payload": False,
        "gor_loss": 16,
        "gonzo_gain": 12,
        "timeout": 28,
    },
    "editor": {
        "html": "editor.html",
        "resolver": "editor",
        "has_payload": False,
        "gor_loss": 15,
        "gonzo_gain": 11,
        "timeout": 26,
    },
}

# Where the HTML files live
WEBAPP_DIR = Path(__file__).parent.parent / "webapp"

# Reject initData older than this (seconds)
MAX_AUTH_AGE = 24 * 3600


# ───────────────────────────────────────────────────────────────────
# initData validation
# ───────────────────────────────────────────────────────────────────
def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Returns the parsed Telegram user dict if the signature is valid and fresh.
    Otherwise returns None.
    """
    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    auth_date = int(pairs.get("auth_date", "0") or 0)
    if not auth_date or (time.time() - auth_date) > MAX_AUTH_AGE:
        return None

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, received_hash):
        return None

    user_raw = pairs.get("user")
    return json.loads(user_raw) if user_raw else {}


# ───────────────────────────────────────────────────────────────────
# Routes
# ───────────────────────────────────────────────────────────────────
async def serve_peak(request: web.Request) -> web.Response:
    """
    GET /peak?c=mile_marker_zero&peak_id=abc123
    Serves the correct HTML file for the requested challenge.
    """
    challenge = request.query.get("c", "bat_swarm")
    config = PEAK_REGISTRY.get(challenge)

    if not config:
        return web.Response(status=404, text="No such hallucination.")

    path = WEBAPP_DIR / config["html"]
    if not path.exists():
        return web.Response(status=404, text="Hallucination file missing on disk.")

    return web.Response(body=path.read_bytes(), content_type="text/html")


async def resolve_answer(request: web.Request) -> web.Response:
    """
    POST /api/peak/answer
    Body: { peak_id, challenge, init_data, ...challenge-specific fields }

    Validates the player, calls the correct resolver, returns authoritative result.
    """
    bot_token = request.app["bot_token"]

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad json"}, status=400)

    user = validate_init_data(body.get("init_data", ""), bot_token)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    user_id = user["id"]
    peak_id = body.get("peak_id")
    challenge = body.get("challenge")

    config = PEAK_REGISTRY.get(challenge)
    if not config:
        return web.json_response({"error": "unknown challenge"}, status=400)

    # Lazy import to avoid circular imports
    from challenges import (
        bat_swarm,
        attorneys_advice,
        lizard_loyalty,
        mile_marker_zero,
        # Add the rest as you create the resolver modules:
        # stagger, hitchhiker, bandit, trunk, shark, editor
    )

    resolvers = {
        "bat_swarm": bat_swarm.resolve_webapp,
        "attorneys_advice": attorneys_advice.resolve_webapp,
        "lizard_loyalty": lizard_loyalty.resolve_webapp,
        "mile_marker_zero": mile_marker_zero.resolve_webapp,
    }

    resolver = resolvers.get(challenge)
    if not resolver:
        return web.json_response({"error": "resolver not implemented yet"}, status=501)

    outcome = await resolver(peak_id, user_id, body)

    if outcome is None:
        # Already answered or not a participant
        player = await get_player(user_id)
        return web.json_response({
            "success": False,
            "already": True,
            "gor": player["gor"] if player else 0,
            "gonzo_delta": 0,
            "eliminated": bool(player and player.get("eliminated")),
        })

    return web.json_response(outcome)


async def get_challenge(request: web.Request) -> web.Response:
    """
    POST /api/peak/challenge
    Used by Peaks that need per-player secret content (Attorney memo, Lizard lineup).
    """
    bot_token = request.app["bot_token"]

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "bad json"}, status=400)

    user = validate_init_data(body.get("init_data", ""), bot_token)
    if user is None:
        return web.json_response({"error": "unauthorized"}, status=401)

    challenge = body.get("challenge")
    config = PEAK_REGISTRY.get(challenge)

    if not config or not config.get("has_payload"):
        return web.json_response({"error": "this challenge has no payload"}, status=400)

    from challenges import attorneys_advice, lizard_loyalty

    providers = {
        "attorneys_advice": attorneys_advice.get_webapp_payload,
        "lizard_loyalty": lizard_loyalty.get_webapp_payload,
    }

    provider = providers.get(challenge)
    if not provider:
        return web.json_response({"error": "provider missing"}, status=501)

    payload = await provider(body.get("peak_id"), user["id"])
    if payload is None:
        return web.json_response({"error": "no active challenge for you"}, status=404)

    return web.json_response(payload)


# ───────────────────────────────────────────────────────────────────
# App factory
# ───────────────────────────────────────────────────────────────────
def build_app(bot_token: str) -> web.Application:
    app = web.Application()
    app["bot_token"] = bot_token
    app.add_routes([
        web.get("/", lambda r: web.Response(text="Somewhere around Barstow. OK.")),
        web.get("/peak", serve_peak),
        web.post("/api/peak/challenge", get_challenge),
        web.post("/api/peak/answer", resolve_answer),
    ])
    return app


async def start_web_server(bot_token: str):
    """Call this from main() as a background task next to dp.start_polling."""
    app = build_app(bot_token)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner
