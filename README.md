# Degen Peaks

Mini App challenges for **Fear and Loathing in Degen Vegas: A Savage Journey**.

Telegram WebApp peaks that deliver high-tension, gonzo-flavored micro-games.
Each Peak hits the player's Grip on Reality and Gonzo Score.

## Architecture

- Single process: bot + Mini App backend share the same event loop and database
- Central Peak registry inside `mini_app.py`
- Client reports result → server is the source of truth for GoR / Gonzo
- Strong `initData` validation (HMAC + freshness check)

## Current Peaks

| Challenge Key | File | Mechanic | GoR Loss | Timeout |
|---------------|------|----------|----------|---------|
| `bat_swarm` | `webapp/batswarm.html` | Tap-to-swat | 16 | 28s |
| `attorneys_advice` | `webapp/attorney.html` | Self-redacting memo | 15 | 25s |
| `lizard_loyalty` | `webapp/lizard.html` | Spot the human | 16 | 22s |
| `mile_marker_zero` | `webapp/milemarker.html` | Road-vanishing survival | 16 | 30s |
| `stagger` | `webapp/stagger.html` | Rhythm foot-tap | 15 | 26s |
| `hitchhiker` | `webapp/hitchhiker.html` | Impulse control | 15 | 24s |
| `bandit` | `webapp/bandit.html` | Precision timing | 14 | 22s |
| `trunk` | `webapp/trunk.html` | Memory flash | 15 | 25s |
| `shark` | `webapp/shark.html` | Pseudo-3D highway | 16 | 28s |
| `editor` | `webapp/editor.html` | Sequence memory | 15 | 26s |

## How to dispatch a Peak

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BASE_URL = "https://your-domain.com"

async def dispatch_peak(user_id: int, peak_id: str, challenge: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="ENTER THE HALLUCINATION",
            web_app=WebAppInfo(url=f"{BASE_URL}/peak?c={challenge}&peak_id={peak_id}")
        )
    ]])
    await bot.send_message(user_id, "The desert is watching.", reply_markup=kb)
```

## Local Demo

Just open any HTML file in `webapp/` in a browser. It runs in demo mode automatically.
