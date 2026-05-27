# Away Game Brawler — Handoff Document
**Version:** v1.0.0  
**Date:** 2026-05-23  
**Engine:** Three.js r128 · Isometric orthographic camera · Tone.js SFX  
**Main file:** `C:\Users\q\Desktop\away_game_brawler.html` (~205 KB — code only)  
**Assets:** `C:\Users\q\Desktop\away_game_brawler_files\` (atlases + skyline, ~16 MB)  
**Serving:** `python -m http.server 8765 --directory C:/Users/q/Desktop`, then open `http://localhost:8765/away_game_brawler.html`

> The game is **no longer a single self-contained file**. The HTML must sit next to the
> `away_game_brawler_files/` folder (relative paths). It needs to be served over HTTP
> (the python command above); opening via `file://` may not load the textures.

---

## ⚠️ CRITICAL — how to edit this file safely

1. **The `autofix-bot` plugin corrupts large files.** It hooks the Edit/Write tools, extracts the
   inline `<script>` to `away_game_brawler.check.js`, reformats, and rewrites the HTML — which
   previously truncated the giant embedded base64 and silently reverted edits. It has been
   **disabled** in `~/.claude/settings.json` (`enabledPlugins.autofix-bot: false`). Keep it off.
2. **The live HTML is kept read-only** as a safety net. Before editing, clear it:
   - PowerShell: `Set-ItemProperty 'C:\Users\q\Desktop\away_game_brawler.html' IsReadOnly $false`
   - or `attrib -R "C:\Users\q\Desktop\away_game_brawler.html"`
   Re-protect when done (`IsReadOnly $true`) if autofix-bot is ever re-enabled.
3. Now that the base64 is **out of the HTML**, the file is ~205 KB and edits normally in any editor.
   Bash/PowerShell writes do NOT trigger autofix-bot; the Edit/Write tools do.
4. Helper scripts used during the split live in `%TEMP%` (`extract_split.py`, `patch_all.py`,
   `integrity.py`, etc.) and can be reused/deleted.

---

## File Layout

```
C:\Users\q\Desktop\
  away_game_brawler.html              ← main game (code only, ~205 KB, read-only)
  away_game_brawler_HANDOFF.md        ← this document
  away_game_brawler_v1.0.0.html       ← versioned backup copy (runs with the assets folder)
  away_game_brawler_v1.0.0_backup.zip ← complete backup (HTML + assets, ~15.6 MB)
  away_game_brawler.check.js          ← autofix-bot leftover artifact (safe to delete)

  away_game_brawler_files\            ← REQUIRED runtime assets
    blue.png    (5120×2048, 20 cols)  enemy skin
    red.png     (5120×2048, 20 cols)  enemy skin
    black.png   (5120×2048, 20 cols)  enemy skin (Tank)
    hero.png    (7168×2048, 28 cols)  player
    skyline.jpg                       title-screen background

  away_game_brawler_assets\           ← source art / PNG components (not loaded at runtime)
```

`SPRITE_DATA` in the HTML is now just a small path map:
```js
const SPRITE_DATA = {"blue":"away_game_brawler_files/blue.png", "red":"...", "black":"...", "hero":"..."};
```
`loadAtlas(name, url)` sets `img.src = url`, so it works with these paths exactly as it did with
data-URIs. To add an atlas: drop a PNG in `away_game_brawler_files/`, add its path to `SPRITE_DATA`,
and `boot()` already loads `blue/red/black/hero` (+ optional `knicks` if present).

---

## What changed in v1.0.0 (this round)

### Architecture
- **Split the game.** Extracted the 4 sprite atlases and the title skyline out of the inline base64
  (which was ~18–21 MB and the source of the corruption/bloat) into real files under
  `away_game_brawler_files/`. HTML dropped from ~21 MB → ~205 KB. Removing base64 overhead also
  shrank total on-disk size.

### Pause / menus
- **On-screen pause button** (`#pause-btn`, circular ❚❚, top-center) — appears once a run starts.
- **Pause menu now has RESUME · RESTART · QUIT.** `quitToTitle()` clears the world and returns to the
  title screen; pressing PLAY again rebuilds a fresh run (PLAY now routes through `restartGame()`).
- Title **QUIT** and **CREDITS** buttons are wired (previously dead).
- ESC still toggles pause.

### HUD (matches the cartoon mockup)
- **"No. 11" shield badge** on the player panel (`.num-shield`).
- Health bar recolored to the orange "away-fan" palette (darker red at low HP).
- **Fixed the broken `?` separators** in the control-hint bar → real `·` middot separators.

### Title screen
- Hero sprite **cycles through every animation** (`TITLE_ANIM_SEQ = idle, run, belt, broom, throw,
  hurt, death`; `TITLE_ANIM_HOLD = 1.6s` each) instead of only the belt attack. `titleSpriteLoop()`
  is now a hoisted function (re-entered when returning to title).
- Canvas **enlarged** to fill the box: internal `448×448`, CSS `width:100%`, container
  `clamp(260px,44vw,460px)` (≈460px at desktop). Note: on very narrow viewports the fixed-width
  menu can squeeze the sprite column — fine on normal/desktop widths.

### Gameplay
- **Attack no longer changes the player's size.** Atlas measurement showed every animation cell
  draws the figure at the same ~236 px height, so the old `1.28×` belt/broom multiplier was making
  the swing pop bigger and the lunge frame read smaller. Replaced with a single constant scale
  (`targetMul = e._baseSpriteMul`), verified the scale stays 1.0 through a `belt` attack.
- **Wider sidewalk.** `SIDEWALK` 2 → **5** (the walkable strip between buildings and the curb is
  now 2.5× wider). Buildings moved inward; roads unchanged; sealed block interior is now 26×26
  (`innerHalf = 30 − SIDEWALK − ROW_DEPTH = 13`).

### Version
- `const GAME_VERSION = "v1.0.0";` — shown bottom-right on the title screen (`#agb-version`) and in
  the pause-menu footer (`ESC to resume · v1.0.0`). Bump this one constant for future versions.

---

## Reference (unchanged systems)

### Atlas row order (8 directions, top→bottom)
`0:S 1:SE 2:E 3:NE 4:N 5:NW 6:W 7:SW`

### HERO_ANIMS (column layout, 28 cols)
```js
idle{col:0,len:4,fps:6,loop}  run{col:4,len:4,fps:12,loop}  hurt{col:8,len:4,fps:14}
death{col:12,len:4,fps:10}    belt{col:16,len:4,fps:10}     broom{col:20,len:4,fps:9}
throw{col:24,len:4,fps:11}
```
Enemy atlases (blue/red/black) are 20 cols / `ENEMY_ANIMS`.

### Controls
| Key | Action | | Key | Action |
|--|--|--|--|--|
| WASD | Move | | ; / C | Block / Parry |
| J / Space | Light attack | | R | Ultimate (meter full) |
| K | Heavy attack | | T | Throw |
| L | Dodge-roll | | Q / E | Rotate camera · Esc Pause |

### World generation
Chunks tile in a 3×3 radius around the player (`updateEndlessCity`). Each chunk = a 60×60 island
(sidewalk + hollow building perimeter + sealed interior) inside an 80×80 chunk; the gap is road.
Key constants: `CHUNK_SIZE 80`, `SIDEWALK 5`, `ROW_DEPTH 12`, building types
`brick|concrete|teal|mustard|plum`. Player spawns at `(0, CHUNK_SIZE/2)` on the border road.

### Combat / AI / pickups / progression / SFX
Unchanged from the prior design: 3-light→finisher chains, heavy breaks, hit-stop + screen shake,
combo pops, rage/ultimate meter, belt/broom weapons; enemy `idle→chase→attack→hurt→death` with
wandering and Knicks-fan ally recruitment; sprite pickups (`coin/heart/star`) + world powerups
(`heal/rage/speed`); localStorage keys `agb_best / agb_totalXP / agb_unlocks / agb_volume / agb_zoom`;
wave objectives `clear / reach / captain` with a level-up overlay; Tone.js SFX
(`punch/punch2/ko/parry/special/ult`).

---

## Backups
- `away_game_brawler_v1.0.0.html` — a runnable copy (uses the shared `away_game_brawler_files/`).
- `away_game_brawler_v1.0.0_backup.zip` — complete portable backup (HTML + all 5 assets). Unzip
  anywhere and serve to restore. **Both reflect the current v1.0.0 (wider sidewalk + version).**

To cut a new backup after edits: copy the HTML to `away_game_brawler_<ver>.html` and zip it together
with `away_game_brawler_files/`.

---

## Not yet done / next steps
- **Renderer fill bug:** in some window sizes the WebGL canvas doesn't cover the whole window (grey
  margins). The `resize` handler updates camera + `renderer.setSize`, but worth checking it fires on
  the initial layout and matches `devicePixelRatio`.
- **Throwables:** `T` plays the throw animation but no projectile is spawned/wired yet.
- **Title sprite on narrow screens:** the menu can squeeze the (now larger) sprite to ~0 width on
  phones; consider stacking the title layout under a width breakpoint.
- Enemy variety (rusher/heavy/thrower), captain attack patterns, Settings/Credits content, Knicks
  ally atlas — all still open from the original plan.
