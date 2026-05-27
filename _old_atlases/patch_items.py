"""
Embeds items_atlas.png into away_game_brawler.html:
1. Adds "items" key to SPRITE_DATA
2. Adds ITEM_ANIMS constant after HERO_ANIMS
3. Adds loadAtlas('items',...) in boot()
4. Adds pickup spawn logic and throwable item system stub
"""
import re, json, base64

HTML_PATH  = 'C:/Users/q/Desktop/away_game_brawler.html'
ATLAS_PATH = 'C:/Users/q/Desktop/_brawler_atlases/items_atlas.png'

with open(ATLAS_PATH, 'rb') as f:
    ITEMS_B64 = 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

with open(HTML_PATH, 'r', encoding='utf-8', newline='') as f:
    src = f.read()

ORIG_LEN = len(src)

# ── 1. ADD "items" to SPRITE_DATA ────────────────────────────────────────────
# SPRITE_DATA is a JSON.parse("...") on one line.
# Strategy: decode, add key, re-encode.
m = re.search(r'const SPRITE_DATA = JSON\.parse\("(.+?)"\);', src, re.DOTALL)
assert m, "SPRITE_DATA not found"

raw = m.group(1).replace('\\\\', '\\').replace('\\"', '"')
data = json.loads(raw)

if 'items' not in data:
    data['items'] = ITEMS_B64
    json_str = json.dumps(data, separators=(',', ':'))
    escaped  = json_str.replace('\\', '\\\\').replace('"', '\\"')
    new_line = f'    const SPRITE_DATA = JSON.parse("{escaped}");\n'
    # Replace old line
    old_line = src[m.start():m.end()+1]   # +1 for \n
    src = src[:m.start()] + new_line + src[m.end()+1:]
    print(f'Step 1: items key added ({len(ITEMS_B64)//1024} KB base64)')
else:
    print('Step 1: items key already present, skipping')

# ── 2. ADD ITEM_ANIMS constant after HERO_ANIMS block ────────────────────────
ITEM_ANIMS_JS = """
    const ITEM_ANIMS = {
        basketball : { col:0,  len:4, fps:10 },
        bottle     : { col:4,  len:4, fps:10 },
        brick      : { col:8,  len:4, fps:8  },
        metrocard  : { col:12, len:4, fps:12 },
        coin       : { col:16, len:4, fps:6  },
        star       : { col:20, len:4, fps:6  },
        heart      : { col:24, len:4, fps:6  },
        boot       : { col:28, len:4, fps:10 },
    };
    // ITEM_ATLAS cols: 8 items × 4 frames = 32 cols, each 256px, 1 row
"""

HERO_ANIMS_END = "        throw:  { col:24, len:4, fps:11, loop:false },\r\n    };"
if HERO_ANIMS_END not in src:
    HERO_ANIMS_END = "        throw:  { col:24, len:4, fps:11, loop:false },\n    };"

if 'ITEM_ANIMS' not in src:
    assert HERO_ANIMS_END in src, "HERO_ANIMS end not found"
    src = src.replace(HERO_ANIMS_END, HERO_ANIMS_END + ITEM_ANIMS_JS, 1)
    print('Step 2: ITEM_ANIMS added')
else:
    print('Step 2: ITEM_ANIMS already present, skipping')

# ── 3. LOAD items atlas in boot() ────────────────────────────────────────────
BOOT_TASKS_ANCHOR = "        const tasks=[\n            loadAtlas('blue', SPRITE_DATA.blue),"

if "loadAtlas('items'" not in src:
    ITEMS_LOAD = """        if(SPRITE_DATA.items) tasks.push(loadAtlas('items', SPRITE_DATA.items, 32, 1));
"""
    # Insert after knicks loader
    KNICKS_LINE = "        if(SPRITE_DATA.knicks) tasks.push(loadAtlas('knicks', SPRITE_DATA.knicks));"
    assert KNICKS_LINE in src, "knicks loader line not found"
    src = src.replace(KNICKS_LINE, KNICKS_LINE + '\n' + ITEMS_LOAD, 1)
    print('Step 3: items atlas loader added')
else:
    print('Step 3: items loader already present, skipping')

# ── 4. ADD pickup spawning + throwable item system ───────────────────────────
PICKUP_SYS = """
    // ---- PICKUPS & THROWABLES -----------------------------------------------
    // Pickup types: coin (+10 XP), heart (+20 HP), star (+10 special)
    const PICKUP_DEFS = {
        coin  : { anim:'coin',  onCollect: p => { awardXP(10); showToast('+10 XP'); } },
        heart : { anim:'heart', onCollect: p => { const h=Math.min(p.maxHp, p.hp+20); p.hp=h; updateHealthUI(); showToast('+20 HP'); } },
        star  : { anim:'star',  onCollect: p => { STATE.special=Math.min(100,STATE.special+10); updateSpecialUI(); showToast('+POWER'); } },
    };
    // Throwable types: basketball, bottle, brick, metrocard, boot
    const THROW_DEFS = {
        basketball : { anim:'basketball', dmg:18, speed:18, range:22 },
        bottle     : { anim:'bottle',     dmg:14, speed:20, range:18 },
        brick      : { anim:'brick',      dmg:24, speed:12, range:14 },
        metrocard  : { anim:'metrocard',  dmg:10, speed:28, range:28 },
        boot       : { anim:'boot',       dmg:20, speed:15, range:20 },
    };
    function spawnPickup(type, x, z){
        if(!TEX['items']) return;
        const def = PICKUP_DEFS[type]; if(!def) return;
        const anim = ITEM_ANIMS[def.anim];
        const mat = new THREE.SpriteMaterial({ map: TEX['items'].texture, transparent:true });
        const sp  = new THREE.Sprite(mat);
        sp.scale.setScalar(2.2);
        sp.position.set(x, 1.1, z);
        scene.add(sp);
        const pu = { type:'pickup', kind:type, mesh:sp, x, z, def,
                     frame:0, frameTimer:0, alive:true };
        STATE.pickups = STATE.pickups || [];
        STATE.pickups.push(pu);
    }
    function tickPickups(dt){
        if(!STATE.pickups || !STATE.pickups.length) return;
        const COLS = 32; // items atlas columns
        STATE.pickups = STATE.pickups.filter(pu => {
            if(!pu.alive){ scene.remove(pu.mesh); return false; }
            // Animate sprite
            pu.frameTimer += dt;
            const fps = ITEM_ANIMS[pu.def.anim]?.fps || 6;
            if(pu.frameTimer >= 1/fps){
                pu.frameTimer = 0;
                pu.frame = (pu.frame+1) % 4;
            }
            const col  = ITEM_ANIMS[pu.def.anim].col + pu.frame;
            const cols = COLS;
            const rows = 1;
            const u = col / cols, v = 0;
            const uw = 1 / cols, uh = 1 / rows;
            const tex = TEX['items'].texture;
            tex.offset.set(u, v);
            tex.repeat.set(uw, uh);
            pu.mesh.material.map = tex;
            pu.mesh.material.needsUpdate = true;
            // Collect check
            const pl = STATE.player;
            if(pl){
                const dx = pl.mesh.position.x - pu.x;
                const dz = pl.mesh.position.z - pu.z;
                if(dx*dx+dz*dz < 2.5*2.5){
                    pu.def.onCollect(pl);
                    scene.remove(pu.mesh);
                    return false;
                }
            }
            return true;
        });
    }
"""

if 'PICKUP_DEFS' not in src:
    # Insert before injectShell
    INJECT_ANCHOR = '    (function injectShell(){'
    assert INJECT_ANCHOR in src, "injectShell not found"
    src = src.replace(INJECT_ANCHOR, PICKUP_SYS + '    ' + INJECT_ANCHOR[4:], 1)
    print('Step 4: pickup system added')
else:
    print('Step 4: pickup system already present, skipping')

# ── 5. HOOK tickPickups into the game loop ────────────────────────────────────
GAMELOOP_HOOK = '        // AI + movement'
if 'tickPickups' not in src:
    src = src.replace(GAMELOOP_HOOK,
        '        tickPickups(dt);\n' + GAMELOOP_HOOK, 1)
    print('Step 5: tickPickups hooked into game loop')
else:
    print('Step 5: already hooked, skipping')

# ── 6. SPAWN pickups when enemies die ────────────────────────────────────────
DEATH_HOOK = "        if(this.hp <= 0 && !this.dead){"
PICKUP_SPAWN_CODE = """        if(this.hp <= 0 && !this.dead){
            // Chance to drop a pickup on death
            if(this.team === 'enemy'){
                const roll = Math.random();
                if(roll < 0.18) spawnPickup('coin',  this.mesh.position.x, this.mesh.position.z);
                else if(roll < 0.25) spawnPickup('heart', this.mesh.position.x, this.mesh.position.z);
                else if(roll < 0.30) spawnPickup('star',  this.mesh.position.x, this.mesh.position.z);
            }"""

if 'spawnPickup' not in src.split('PICKUP_DEFS')[1][:500]:
    if DEATH_HOOK in src:
        src = src.replace(DEATH_HOOK, PICKUP_SPAWN_CODE, 1)
        print('Step 6: pickup drop on enemy death added')
    else:
        print('Step 6: death hook not found, skipping')
else:
    print('Step 6: already added, skipping')

# ── WRITE BACK ────────────────────────────────────────────────────────────────
with open(HTML_PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

print(f'\nDone. {ORIG_LEN:,} -> {len(src):,} bytes (+{len(src)-ORIG_LEN:,})')
