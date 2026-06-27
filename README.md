# Farm Prototype

A tiny weekend-scoped slice of the bigger Stardew-Valley-style idea:
till soil, plant and harvest two crops, sell at the market, and build
a friendship meter with one NPC through talking and gift-giving.

This is deliberately **not** the full game. It's a vertical slice -
small enough to finish in a weekend, built on a foundation (farming,
economy, relationships) that's meant to grow rather than get thrown
away.

## What you need before starting

- **Python 3.10 or newer.** Check what you have with:
  ```
  python3 --version
  ```
  If that's missing or too old, get it from https://python.org.

That's it - everything else below installs into this project only.

## 1. Set up a virtual environment

A virtual environment keeps this project's dependencies separate from
anything else on your system. From inside the `farm_prototype` folder:

```bash
python3 -m venv .venv
```

Activate it (you'll need to do this every time you open a new
terminal to work on the project):

- **Mac/Linux:** `source .venv/bin/activate`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

You'll know it worked because your terminal prompt will start with
`(.venv)`.

## 2. Install dependencies

With the virtual environment active:

```bash
pip install -r requirements.txt
```

This installs `pygame-ce` (the game library, used for local desktop
testing) and `pygbag` (the tool that packages the game to run in a
browser).

## 3. Run it on your desktop

```bash
python main.py
```

A window should open. This is the fastest way to iterate while you're
building - way faster than re-exporting to the browser every time you
change a line of code.

**Controls:**
- Move: WASD or arrow keys
- Interact: `E` (till soil / plant / harvest / talk to Maple / open
  the Market, depending on what you're standing near)
- Gift: `G` (give Maple one of whatever crop you're carrying, if
  you're standing close to her)
- Select seed: `1` for Carrot, `2` for Potato

The same actions are available as on-screen buttons (bottom-left
d-pad, bottom-right Interact/Gift, top-left seed selector), which is
what you'll actually use once this is running on a phone.

## 4. Run it in a browser (this is what makes it work on PC *and* mobile)

```bash
python -m pygbag .
```

The first run will be slower - it downloads the Python/Pygame
WebAssembly runtime and caches it locally. Once it's done, it starts a
local server. Open the URL it prints (usually `http://localhost:8000`)
in a browser on your computer, or on your phone if it's on the same
WiFi network as your computer.

Every time you change the code, you need to stop (`Ctrl+C`) and rerun
`python -m pygbag .` to repackage it.

## 5. Run the tests

```bash
python -m unittest discover -s tests -t .
```

This checks the buy/sell/inventory rules (`game/systems/`) without
needing a display at all. It's intentionally small - just enough to
catch a broken pricing rule before you notice it by playing - not a
full test suite. As you add more systems, the ones with real logic
worth protecting (not just rendering) are the ones worth adding tests
for.

## How the code is organized

```
farm_prototype/
  main.py                   - entry point; the only pygbag-specific code lives here
  game/
    config.py                - every tunable number and layout position
    world.py                 - the single screen: player, tiles, NPC, shop, HUD, input
    entities/
      crop.py                 - one planted crop's growth + drawing
      npc.py                   - the NPC's friendship meter + dialogue
    systems/
      inventory.py             - seed/crop counts (no pygame dependency)
      economy.py                - gold + buy/sell rules (no pygame dependency)
  tests/
    test_systems.py            - tests for the two modules above
```

**Why `inventory.py` and `economy.py` have no pygame imports:** they're
pure data and rules. That's what makes them easy to test, and it's
also what makes them safe to reuse later (e.g. if you ever wanted a
save/load system, these are the objects you'd serialize).

**Why there's only one `World` class instead of separate "scenes":**
the whole game is one non-scrolling screen right now. Splitting into a
scene system before there's a second screen to transition to would be
solving a problem you don't have yet. When you add a second area (a
fishing dock, say), that's the right time to introduce one.

**Why the NPC's friendship meter lives directly on `NPC`** instead of
a separate "Relationship" class: there's only one NPC. If you add a
second NPC and find yourself copy-pasting friendship logic, pull it
out into its own class then - not before.

## How to extend this

- **Add a third crop:** add an entry to `CROPS` in `game/config.py`.
  Nothing else needs to change.
- **Add a second NPC:** create another `NPC(...)` instance in
  `World.__init__`, give them a position in `config.py`, and add an
  `_near_<name>` check similar to `_near_npc`.
- **Add a second area:** this is the point to introduce a simple state
  machine (e.g. `self.current_area = "farm"` and an `if/elif` in
  `update`/`draw`, or a proper scene-manager class once you have 3+
  areas) rather than letting `World` keep growing.

## A note on version control

This isn't required to play the prototype, but if you plan to keep
building on this:

```bash
git init
git add .
git commit -m "Initial farm prototype"
```

The `.gitignore` is already set up to exclude the virtual environment
and pygbag's build cache, so neither gets committed by accident. For a
solo weekend project, committing directly to `main` as you go is fine;
once you're adding bigger features (a second area, save/load), it's
worth branching per-feature so a half-finished change doesn't leave
`main` in a broken state.
