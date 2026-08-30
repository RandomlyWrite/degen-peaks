"""
Mile Marker Zero — desert highway survival Peak

The road behind the car is vanishing in real time.
Player must stay ahead of the rising void while dodging
bats, lizards, and the Attorney's occasional control inversions.
"""

from db.database import record_peak_response, update_player_stats, get_player

GOR_LOSS = 16
GONZO_GAIN = 12

# Shared with the rest of the peak system
_responded: dict[str, set[int]] = {}
_pending: dict[str, set[int]] = {}


async def resolve_webapp(peak_id: str, user_id: int, body: dict) -> dict | None:
    """
    Called by the Mini App backend when the player finishes the challenge.
    Client reports hit/survived_s. Server owns GoR / Gonzo truth.
    """
    if user_id in _responded.get(peak_id, set()):
        return None  # already answered

    _responded.setdefault(peak_id, set()).add(user_id)
    _pending.get(peak_id, set()).discard(user_id)

    hit = bool(body.get("hit"))
    survived = int(body.get("survived_s", 0))

    await record_peak_response(peak_id, user_id, success=hit)

    if hit:
        await update_player_stats(user_id, gonzo_delta=GONZO_GAIN)
    else:
        await update_player_stats(user_id, gor_delta=-GOR_LOSS)

    p = await get_player(user_id)
    return {
        "success": hit,
        "gor": p["gor"] if p else 0,
        "gonzo_delta": GONZO_GAIN if hit else 0,
        "eliminated": bool(p and p["eliminated"]),
        "survived_s": survived,
    }


async def get_webapp_payload(peak_id: str, user_id: int) -> dict | None:
    """
    This challenge has no per-player secret content.
    """
    return {}
