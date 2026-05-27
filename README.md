# Street Sweeper Brawler

A browser-based isometric brawler. Three.js renderer, Tone.js audio, sprite-atlas
animation system with 8 facings per character. Single self-contained HTML file
plus image atlases.

## Run it

Serve the folder over a static HTTP server (the engine fetches PNGs by relative
URL, so opening the HTML via `file://` will fail CORS for image getImageData):

```
python -m http.server 8765
# then open http://localhost:8765/away_game_brawler.html
```

Backtick (`) opens the dev menu — spawn enemies, captains, boss, pickups, and
preview any atlas across all 8 facings in the Sprite Lab.

## Layout

| Path | Purpose |
|---|---|
| `away_game_brawler.html` | Main game (HTML + inline JS + CSS) |
| `away_game_brawler_files/` | Core atlases (hero/blue/red/black/hawks) + skyline |
| `away_game_brawler_assets/character_atlases/` | Generated character atlases (celtics_0, sixers_21, hawks_v2, heavy_bball, fighter_f, ...) |
| `away_game_brawler_assets/New Characters Input/` | Source AI sheets fed into the combiner |
| `combine_atlases.py` | Grid-detecting Python combiner — converts AI source sheets into clean 4-frame × N-facing atlases (chroma-key, alpha trim, upscale, hold-frame fill, cross-row fallback) |
| `combine_atlases.html` | Browser-based companion combiner with drag&drop slots |
| `dev_menu/` | Portable dev-menu library extracted from this game — drop into other game projects (see `dev_menu/README.md`) |
| `away_game_brawler_v1.0.0.html` | Earlier release snapshot |
| `away_game_brawler_HANDOFF.md` | Original handoff notes |
| `_old_atlases/` | Legacy atlas variants kept for reference |

## Regenerating character atlases

```
python combine_atlases.py
```

Edits the PNGs in `away_game_brawler_assets/character_atlases/` from sources in
`away_game_brawler_assets/New Characters Input/`. Reload the game; auto-trim runs
on load and the new atlases appear in Sprite Lab.

## Character roles (gameplay)

| Atlas | Role |
|---|---|
| `hero` | Player |
| `blue`, `red`, `black` | Regular enemies |
| `celtics_0` | Mid-boss captain (fast + strong) |
| `sixers_21` | Mid-boss captain (slow + strong) |
| `hawks_v2` | Main boss (ranged, hawks-jersey allies rally to help) |
| `heavy_bball`, `fighter_f` | Ally recruits — defeated enemies convert into these |
