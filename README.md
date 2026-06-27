# Farm Prototype

A small slice of the bigger Stardew-Valley-style idea: till soil,
plant and harvest two crops, sell at the Market, build friendship with
two NPCs, and fish at the Dock (unlocked with gold). The farm itself
now has a barn, a small chicken pen with eggs to collect, scattered
rocks and trees that actually block movement, and a locked shed that
hints at something not built yet.

This is deliberately **not** the full game. It's a vertical slice -
built on a foundation (farming, economy, relationships, areas,
collision) that's meant to grow rather than get thrown away.

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
- Interact: `E` (till soil / plant / harvest / talk to whichever NPC
  is nearby / open the Market / use the Dock gate / cast and reel in a
  fishing line, depending on what you're standing near)
- Gift: `G` (give the nearby NPC one item from your inventory - crop
  or fish, whatever you're holding)
- Select seed: `1` for Carrot, `2` for Potato

There are two NPCs to find on the farm: **Maple** (top-left, warm and
friendly) and **Felix** (bottom-right, gruff at first but warms up).

On the right edge of the farm is a gate to the **Dock** - it costs
gold to "build the path" the first time you interact with it (one-time
cost, see `DOCK_UNLOCK_COST` in `game/config.py`). Once unlocked, the
Dock has three fishing spots: stand near one, press Interact to cast,
wait for "Bite!", then press Interact again quickly to reel it in.
Catch is random between Minnow, Bass, and Trout - sell them at the
Market like crops.

The farm also has a **barn**, a small **chicken pen** (the chickens
just wander - they're ambient, not interactive), and a **nest** you
can collect an egg from periodically. Rocks, trees, and the buildings
all physically block movement now - this is the first thing in the
prototype with real collision. There's also a boarded-up **shed** in
the corner that you can't get into; interacting with it just shows a
flavor-text message. That's intentional - see "Loose threads" below.

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
    config.py                - tunable numbers and world layout positions
    npc_data.py               - per-NPC content: name, position, color, dialogue
    world.py                  - the single screen: player, tiles, NPCs, shop, HUD, input
    entities/
      crop.py                  - one planted crop's growth + drawing
      npc.py                    - friendship meter + dialogue selection, driven by npc_data.py
      obstacle.py                - collidable scenery (rocks/trees/buildings), incl. the mystery shed
      animal.py                   - ambient wandering chickens (no collision)
      nest.py                      - periodically-refreshing egg source
    systems/
      inventory.py              - seed counts + held items, crops or fish alike (no pygame dependency)
      economy.py                 - gold + buy/sell rules (no pygame dependency)
  tests/
    test_systems.py             - tests for the two modules above
```

**Why `inventory.py` and `economy.py` have no pygame imports:** they're
pure data and rules. That's what makes them easy to test, and it's
also what makes them safe to reuse later (e.g. if you ever wanted a
save/load system, these are the objects you'd serialize).

**Why there's only one `World` class instead of separate "scenes":**
now that there are two areas (farm and dock), `World` tracks which one
is active with a single `self.current_area` flag and branches on it in
`update`/`draw` (see `_draw_farm_area` vs `_draw_dock_area`) - both
areas still share the same coordinate space and the same class. A
full scene-manager class (each area as its own object, with its own
lifecycle) would be solving a problem that doesn't exist yet. If a
third area gets added and the `if/elif` branching starts feeling
unwieldy, that's the signal to introduce one - not before.

**Why the NPC's friendship meter lives directly on `NPC`** instead of
a separate "Relationship" class: each `NPC` instance already tracks
its own friendship value independently, so adding a second character
(Felix) only required new *data* in `npc_data.py` - name, position,
color, dialogue, gift reactions - with no changes to the friendship
logic itself. That's the actual signal for whether a class needs
splitting up: if a second use case needs you to copy-paste logic, pull
it out then. Here, it didn't, so it stayed as-is.

**Why collision uses simple rectangles for everything**, even round
things like rocks: a rock's hitbox doesn't need to be circular for the
player to believe it's a rock - it only needs to feel roughly right
and be cheap to reason about. Mixing circle math for some obstacles
and rect math for others (the barn) would have doubled the collision
code for a difference players won't notice. The collision box for
each obstacle is also deliberately a little smaller than what gets
drawn, so the interaction radius can comfortably reach an obstacle's
center (needed for the shed's message) without the hitbox edge and the
sprite edge feeling like the same line.

**Why chickens don't collide with anything:** they're ambient motion,
not gameplay. Giving them collision would mean either the player
getting stuck on a wandering chicken (annoying) or writing
chicken-vs-obstacle collision too (more code for zero gameplay value
right now). If a future mechanic genuinely needs to catch or herd
them, that's a real reason to revisit this - not before.

## How to extend this

- **Add a third crop:** add an entry to `CROPS` in `game/config.py`.
  Nothing else needs to change - it's automatically buyable, sellable,
  and giftable since `SELLABLES` is built from `CROPS` and `FISH`
  combined.
- **Add a fourth fish:** add an entry to `FISH` in `game/config.py`.
  Same deal - shows up in the shop and as a possible catch
  automatically.
- **Add a fourth fishing spot:** add a position to `FISHING_SPOTS` in
  `game/config.py`.
- **Add a third NPC:** add an entry to `NPC_PROFILES` in
  `game/npc_data.py` with a name, position, color, dialogue (one list
  of lines per friendship tier: `stranger`/`friendly`/`close`), and
  gift reactions. Nothing in `world.py` or `npc.py` needs to change -
  `World` builds its NPC list directly from this dictionary.
- **Add a third area:** this is the point where the
  `if self.current_area == "dock": ... else: ...` branching in `World`
  starts being worth replacing with a proper scene-manager class (one
  class per area, each with its own `update`/`draw`, switched by the
  manager). Two areas was fine as a flag; three is where that pattern
  usually stops paying for itself.
- **Add another obstacle (rock, tree, or building):** add an entry to
  `OBSTACLES` in `game/config.py` with a `kind` and a `pos`. To make it
  collidable but silent, leave out `message`; to give it something to
  say when the player interacts nearby (like the shed), include one.
- **Add another animal:** `World._build_npcs`-style, but for chickens
  it's even simpler since they're all identical right now - just bump
  `NUM_CHICKENS` in `game/config.py`. A genuinely different animal
  (say, a cow that gives milk instead of wandering for eggs) would
  warrant its own class alongside `Chicken`, the same way `Obstacle`
  has different `kind`s rather than a different class per rock type.

## Loose threads (on purpose)

- **The shed.** It's deliberately unenterable - it's an `Obstacle`
  with a `message` and nothing else. There's no quest system, no key
  item, no second mechanic hiding behind it yet. When you're ready to
  build whatever's actually in there, `World._nearby_obstacle_with_message`
  is where you'd swap the flavor-text response for a real check (e.g.
  "do you have the key item / have you reached some milestone") and a
  real payoff. Until then, it's a hook, not a half-finished feature -
  it does exactly what it's supposed to do (make you wonder) and
  nothing it's not supposed to do (pretend to be more finished than it
  is).

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
