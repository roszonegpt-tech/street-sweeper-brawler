# Street Sweeper Brawler — Feature Roadmap

Living document. Features grouped by theme. Effort tags are rough order-of-magnitude
estimates: **S** ≈ a session, **M** ≈ a weekend, **L** ≈ a week+, **XL** ≈ multi-week.
Dependencies noted where one feature blocks/unlocks another.

Existing features are checked. Items 1–15 are your original list. Items 16–30 are
additions that complement the arcade DNA already in place.

---

## 🎮 Combat Feel & Player Expression

### 1. Crowd Hype Meter · **M**
Fans on the sidewalks cheer louder as combos chain. A meter at the top of the screen
fills with combo hits, dodges, parries. At HYPE level 1 → +20% score, level 2 → faster
rage gain, level 3 → ultimate auto-charges over time. Drops slowly when idle, faster
when player takes damage. Cosmetic: sidewalk crowd density + audio mix swells.
*Depends on:* existing combo counter. *Unlocks:* hype-fueled finishers (#8).

### 7. Taunt Button · **S**
New input (probably `T` on keyboard, dedicated UI button on mobile). Plays a 1.2 s
locked-out taunt animation. During the lockout, the player can't move but **builds
hype at 4× rate** and **regenerates 8% rage**. Risky in a crowd. Bonus: taunting in
the boss's face grants a one-time damage buff.
*Depends on:* taunt anim cells on hero atlas (currently missing → reuse `idle` with
a fist-pump overlay until a proper taunt frame is drawn).

### 8. Finisher Moves · **M**
Every 3-hit combo's last hit upgrades into a flashy finisher. Pool of finishers
depends on equipped weapon: belt-spin, broom-uppercut, shoulder-check, chair-slam,
foam-finger-poke. Slow-mo pop on connect + extra knockback + screen flash.
*Depends on:* extra anim cells per weapon (or reuse with VFX overlay). *Pairs with:*
hit-pause polish (#22).

### 14. Style Grade · **S**
After each wave, show a grade card: D/C/B/A/S. Scoring:
- Combos landed × 5
- Perfect parries × 25
- Dodges × 8
- Finishers × 40
- No-damage bonus +100, no-block bonus +50
S grade unlocks a brief score multiplier the next wave.
*Depends on:* per-wave session tracking (mostly already in `STATE`).

### 22. Hit-Pause Tuning · **S** *(new)*
Already partially present (`triggerHitStop`). Add tiers: light hits 60 ms, heavy 100
ms, finisher 180 ms, parry 220 ms. Tightens the arcade feel and makes finishers feel
weightier without new art.

### 23. Stance Toggle · **M** *(new)*
Press a key to swap between **Sweep** (current — quick belt/broom, +speed) and
**Brawl** (slower, +damage, super armor on heavy attack). Adds depth for high-skill
players without doubling content cost.

---

## 👊 Enemies & Bosses

### 2. Rival Team Ambushes · **M**
Every 4–6 waves, a 4-fan squad of rival colors charges in. Spawn vectors: alley
mouths, parked bus doors, subway grates. Each rival color has one behavioral quirk:
- **Yellow (Lakers)** — kite at range, throw foam basketballs
- **Green (Celtics)** — shoulder-charge dash-in
- **Red (Bulls)** — bull-rush, ignores knockback for 1 hit
- **Black (Nets)** — drops smoke bomb on death, blocks vision
*Depends on:* existing enemy AI + small per-color tweaks. *Pairs with:* #16 District map.

### 5. Mid-Boss Captains · **L**
Captains spawn before the main boss with bespoke special moves:
- **Tatum (Celtics)** — charge-dash that knocks player through trash cans
- **Embiid (Sixers)** — elbow throw with super armor windup
- **Knicks Captain** — calls 3 backup fans on a 12 s cooldown
- *Future:* Lakers Captain — taunts to give nearby fans +speed
*Status:* `CAPTAIN_PROFILES` already exists for celtics_0 & sixers_21 (stat tuning
done). This item is about adding their **special moves**, not just stats. *Depends
on:* finisher tech (#8) — the special moves use the same anim+VFX system.

### 12. Mascot Rival Battles · **XL**
A roster of mascot bosses, each with one signature ridiculous special:
- **Hawks (current)** — t-shirt cannon barrage (already wired as `attack2`)
- **Phoenix Suns mascot** — flame-stilts dash
- **Raptors mascot** — back-flip area-stun
- **Knicks mascot** — calls in a NYC subway car (#11 connection)
Each mascot gets a 3 s intro card with name + comically dramatic title.
*Depends on:* atlas per mascot, intro overlay system. *Pairs with:* #15 unlockables.

### 6. Ally Recruit System · **M**
*Status:* partially shipped — `makeAlly` / `scheduleRecruit` already exist; defeated
enemies have a chance to convert into `heavy_bball` / `fighter_f`. Remaining work:
- Ally HP bar above their head
- "RECRUIT" button prompt over stunned enemies (manual recruit option)
- Allies persist between waves with diminishing HP (encourages protecting them)
- Cap on simultaneous allies (currently 3, expose as a perk)

### 18. Rivalry Meter Per Team · **M** *(new)*
For each rival color, track a kill counter. At thresholds:
- 10 kills → that team's captain spawns with +25% HP next time you meet them
- 25 kills → that team's mascot boss intro is replaced with a "you've made enemies"
  variant + extra adds on the field
Pure stat tweaks but creates dynamic "the city remembers" flavor.

---

## 🥤 Items & Pickups

### 3. Environmental Weapons · **M**
Pickup weapons scattered around the city blocks. Each has its own anim hook and a
durability counter that depletes per hit.
- Traffic cone (light, fast)
- Trash can lid (light, blocks one attack)
- Folding chair (heavy, +knockback)
- Foam finger (joke weapon, taunts while attacking — interacts with #7)
- Broomstick (already the default; now durable)
- Pretzel (very heavy, throwable, low durability)
- Soda cup (throwable, leaves slip puddle on landing — interacts with #4)
*Depends on:* per-weapon anim columns (reuse `broom`/`belt` slots) and a pickup spawn
system on chunks.

### 10. Food Pickups · **S**
Dropped from defeated enemies and from broken trash cans:
- 🌭 hot dog → restores 25 HP
- 🍕 pizza → +25% attack speed for 8 s
- 🥤 soda → +25% move speed for 8 s
- 🌮 nachos → reduces incoming damage by 25% for 8 s
- 🍩 donut (rare) → fully refills rage meter
*Depends on:* existing pickup system + new sprite tiles.

### 24. Coin Economy · **M** *(new)*
Defeated enemies drop coins. Spend coins between waves at a vendor cart for:
- Permanent stat upgrades (HP, damage, recruit cap)
- Pre-stocked weapons for the next wave
- Cosmetics (links to #15)
Persists across runs as a soft progression spine without overhauling the wave loop.

### 25. Throwables Pocket · **S** *(new)*
A second small inventory slot for throwable consumables: rotten tomato (stuns),
egg (blinds), firecracker (AoE knockback). Hold-to-aim throw arc indicator.

---

## 🚦 World, Hazards & Set-Pieces

### 4. Street Hazards · **L**
The city should fight back. Hazards spawn semi-randomly each chunk:
- Moving taxis along major roads (damage on contact, drift to a stop if hit hard)
- Steam vents — telegraph circle, then erupt for 1.5 s
- Loose manhole covers — flips up on second step, opens a small pit
- Subway grates — clang on contact, alerts every nearby enemy
- Spilled soda puddle — sliding traction (player AND enemies)
- Construction cones — slow movement, useable as weapons (#3 link)
*Depends on:* chunk-generation hooks (already in `generateChunk`).

### 9. Basketball Court Bonus Area · **M**
1-in-N chunks generate a half-court instead of buildings. Entering triggers a sealed
arena round: 60 s, clear all enemies → unlock a temporary buff (1 wave of double
score / double rage / triple speed) or a permanent perk (one per run).

### 11. Subway Bonus Stage · **L**
Every ~10 waves, the player is pulled into a station. Tile-based interior. Enemies
pour out of arriving train doors for 90 s; survive until the train leaves. Reward:
guaranteed mid-boss spawn next wave, or a rare cosmetic.
*Depends on:* indoor-chunk template (new scene tech).

### 16. District Map · **L** *(new)*
City divided into 4–6 districts. Each district has its own:
- Color palette and skyline silhouette
- Resident rival team (drives #2 ambush color)
- District-specific hazard (e.g. Theater District has runaway carriages,
  Financial District has briefcase-throwing fans)
- District boss (a mascot from #12)
Progress through districts in any order; completing all unlocks the mascot rumble
finale.

### 26. Weather & Time-of-Day · **M** *(new)*
Rain (slick streets, faster speed but less traction), night (crowd is rowdier →
hype builds 30% faster but visibility is lower), morning rush (more taxi traffic).
Pure mood + light gameplay modifier. Each wave can roll a weather modifier.

### 27. Destructible Scenery · **M** *(new)*
Newsstands, fire hydrants (water knockback), trash cans (food drops), parked
scooters (use as weapon). 2-hit breakable. Adds reactive feel to combat.

---

## 📜 Progression & Meta

### 13. Wanted Poster System · **M**
A "Most Wanted Fan" status escalates the longer the run lasts:
- Notoriety tier 1 (wave 5): +1 enemy per spawn, +10% score
- Tier 2 (wave 10): rival ambushes (#2) trigger 2× as often, +25% score
- Tier 3 (wave 20): mascot bosses do a brief cameo intro, +50% score
- Tier 4 (wave 30+): the whole city is hostile — including pedestrians — +100% score
Visible in the HUD as a wanted poster portrait that scribbles in more details as
notoriety rises.

### 15. Unlockable Skins · **L**
Cosmetic items unlock at wave milestones or boss kills:
- Fan jerseys (alternate hero atlas tints)
- Hats (top-cell overlay)
- Sneakers (foot-cell overlay)
- Joke costumes (mascot suit, ref uniform)
*Depends on:* shader/cell-overlay tech, or extra atlas slots.

### 28. Daily Challenge Wave · **S** *(new)*
A fixed seed wave generated from today's date. Single best score per day uploaded
to a local leaderboard (or wired to a remote later). One free retry; second try
costs in-game coins (#24). Drives daily return habit.

### 29. Boss Rush Mode · **M** *(new)*
Unlocked after completing the main mode once. All bosses back-to-back, no waves
between. Time-attack leaderboard.

### 30. Practice Arena · **S** *(new)*
A dev-style arena (already partially exists as the title-screen scene). Player can
pick: which enemies/captain/boss to spawn, weapons available, hazards on/off. No
score, no death — useful for learning matchups and tuning combos. Pairs with the
existing dev menu.

---

## 🎬 Polish & Out-of-Game

### 17. Replays + GIF Export · **L** *(new)*
Record the last 8 s of input + state. After a notable combo, prompt "Save this clip?"
Export as animated GIF using a canvas-based encoder. Shareable in-browser link.
*Depends on:* deterministic playback from inputs (most state is already deterministic
modulo RNG; needs seed capture).

### 19. Announcer Voice Barks · **S** *(new)*
On combo milestones / parries / finishers, an arcade announcer voice cuts in:
"DOUBLE SHIFT!" / "BROOM-IN-ONE!" / "STREET CLEAN!" / "FAN-TASTIC!" Uses Tone.js
or short pre-recorded clips. Massive feel boost for ~2 days of work.

### 20. Couch Co-op (2P) · **L** *(new)*
Second player joins on keyboard or gamepad. Shared screen, shared score, separate
HP. Each player picks a different hero atlas. Pairs nicely with #11 subway stage.

### 21. Photo Mode · **S** *(new)*
Press a key to freeze the game, free-orbit the camera, apply filters and a frame.
Save to PNG. Trivial to add and great for organic social sharing.

---

## 📋 Suggested Build Order

If you want a sequence that snowballs (each feature reusing tech from the previous):

1. **Combat-feel pack** — Hype Meter (#1), Taunt (#7), Hit-Pause Tuning (#22), Style Grade (#14)
2. **Enemy variety pack** — Rival Ambushes (#2), Mid-Boss Captains (#5), Rivalry Meter (#18)
3. **Pickup pack** — Environmental Weapons (#3), Food (#10), Throwables (#25)
4. **World pack** — Street Hazards (#4), Destructible Scenery (#27), Court (#9)
5. **Big set-piece pack** — Subway Bonus (#11), District Map (#16)
6. **Meta pack** — Wanted Poster (#13), Coin Economy (#24), Unlockable Skins (#15)
7. **Polish pack** — Finishers (#8), Announcer (#19), Photo Mode (#21)
8. **Modes pack** — Daily Challenge (#28), Boss Rush (#29), Practice (#30)
9. **Stretch goals** — Mascot Roster (#12), Co-op (#20), Replays (#17), Weather (#26), Stance (#23)

Most of pack 1–4 reuse infrastructure that's already in the codebase (chunk
generation, anim system, dev menu). Packs 5+ require new scene/tech work.

---

## What's Already Done

- ✅ Multi-atlas hero/enemy/boss/captain wiring with per-atlas row counts
- ✅ Auto-trim + chroma-key pipeline for AI-generated source sheets (`combine_atlases.py`)
- ✅ Mid-boss captains spawn (Tatum fast, Embiid slow) — stats only, no special moves yet
- ✅ Hawks mascot main boss with bazooka attack2
- ✅ Hawks-jersey rally AI (#2 partially groundwork)
- ✅ Ally recruit system (partial — see #6 remaining work)
- ✅ Dev menu with full spawn / cheat / sprite-lab kit
- ✅ Minimap with directional player arrow
- ✅ Anti-stuck routine for enemies in buildings
- ✅ Rebrand from "Away Game Brawler" → "Street Sweeper Brawler"

---

Last updated: this commit. Edit freely — this file is the source of truth for the
"where could this go next?" conversation.
