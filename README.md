# Degen Peaks

Mini App challenges for **Fear and Loathing in Degen Vegas: A Savage Journey**.

Telegram WebApp peaks that deliver high-tension, gonzo-flavored micro-games.
Each Peak hits the player's Grip on Reality and Gonzo Score.

## Current Peaks

| Challenge | File | Mechanic |
|-----------|------|----------|
| Bat Swarm | `webapp/batswarm.html` | Tap-to-swat canvas action |
| The Attorney's Advice | `webapp/attorney.html` | Self-redacting memo |
| The Ether Stagger | `webapp/stagger.html` | Rhythm foot-tap |
| The Hitchhiker | `webapp/hitchhiker.html` | Impulse control / thought suppression |
| The One-Armed Bandit | `webapp/bandit.html` | Precision timing reels |
| Trunk Inventory | `webapp/trunk.html` | Memory flash |
| Lizard Loyalty Test | `webapp/lizard.html` | Spot the human |
| The Great Red Shark | `webapp/shark.html` | Pseudo-3D highway steering |
| **Mile Marker Zero** | `webapp/milemarker.html` | **Road-vanishing survival** |
| The Editor's Call | `webapp/editor.html` | Sequence memory (Simon) |

## Mile Marker Zero (new)

The road behind the car is literally disappearing.  
Stay ahead of the rising void, dodge lizards and bats, and survive the Attorney's control inversions.

- **File**: `webapp/milemarker.html`
- **Resolver**: `challenges/mile_marker_zero.py`
- **Challenge key**: `mile_marker_zero`

## Architecture

- Mini Apps are served from the same process as the bot.
- `initData` validation happens server-side.
- Client reports outcome; server applies GoR / Gonzo changes.

See `mini_app.py` for the routing and validation layer.
