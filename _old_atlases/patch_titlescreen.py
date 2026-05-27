"""
Replaces the old card-style title screen with the new full-screen
TSX-inspired design. Uses position-based splicing to avoid CRLF/encoding issues.
"""
import re

HTML_PATH = 'C:/Users/q/Desktop/away_game_brawler.html'
SKYLINE_B64_PATH = 'C:/Users/q/Desktop/_brawler_atlases/skyline_b64.txt'

with open(SKYLINE_B64_PATH, 'r') as f:
    SKYLINE = f.read().strip()

with open(HTML_PATH, 'r', encoding='utf-8', newline='') as f:
    src = f.read()

ORIG_LEN = len(src)

# ── helper: splice by anchor strings ─────────────────────────────────────────
def splice(text, start_anchor, end_anchor, replacement, start_offset=0, end_offset=0):
    i = text.find(start_anchor)
    assert i != -1, f"start_anchor not found: {start_anchor[:60]!r}"
    j = text.find(end_anchor, i)
    assert j != -1, f"end_anchor not found: {end_anchor[:60]!r}"
    j += len(end_anchor)
    return text[:i + start_offset] + replacement + text[j + end_offset:]

# ── 1. INSERT NEW CSS before the closing backtick of the css template literal ─
# Anchor: the last line of the css block (unique)
CSS_ANCHOR = '.agb-power-chip{ background:rgba(20,12,6,.85)'
CSS_END_ANCHOR = 'letter-spacing:1px; }'   # end of power-chip rule

NEW_CSS = r"""
        /* ───── TITLE SCREEN ───── */
        #agb-title-screen{
            position:fixed; inset:0; z-index:50; background:#88cce6;
            display:flex; align-items:center; justify-content:center;
            overflow:hidden; transition:opacity .4s;
        }
        #agb-title-screen.hidden{ opacity:0; pointer-events:none; }
        .agb-title-skyline{
            position:absolute; inset:0; width:100%; height:100%;
            object-fit:cover; object-position:bottom; pointer-events:none;
        }
        .agb-cloud{ position:absolute; pointer-events:none; opacity:.85; }
        .agb-cloud-a{ top:40px;  animation: agbCloudDrift 40s linear infinite; }
        .agb-cloud-b{ top:128px; animation: agbCloudDrift 25s linear infinite; animation-delay:-10s; }
        @keyframes agbCloudDrift{
            0%  { transform:translateX(110vw); }
            100%{ transform:translateX(-140%); }
        }
        .agb-cloud-body{
            position:relative; background:white; border-radius:999px;
            box-shadow:0 8px 0 0 #dbeafe;
        }
        .agb-cloud-puff{ position:absolute; background:white; border-radius:50%; }
        #agb-logo-main{
            font-size:clamp(52px,7vw,88px); font-weight:900; color:#e85d34;
            letter-spacing:-2px; margin:0; line-height:1;
            -webkit-text-stroke:5px white;
            text-shadow:0px 10px 0px #4a2511;
            paint-order:stroke fill;
        }
        #agb-logo-sub{
            background:white; padding:6px 22px; border-radius:999px;
            border:4px solid #e85d34; box-shadow:0 6px 0 0 #4a2511;
            transform:rotate(3deg); display:inline-block;
            color:#e85d34; font-weight:900; font-size:22px; letter-spacing:4px;
            margin-top:2px; float:right; margin-right:12px;
        }
        .agb-menu-btn{
            color:white; font-weight:900; font-size:24px;
            padding:14px 0; border-radius:999px;
            border:6px solid #4a2511;
            box-shadow:0 8px 0 0 #4a2511;
            cursor:pointer; user-select:none;
            transition:transform .08s, box-shadow .08s;
            width:280px; text-align:center;
            font-family:inherit; letter-spacing:1px;
        }
        .agb-menu-btn:hover { transform:translateY(4px); box-shadow:0 4px 0 0 #4a2511; }
        .agb-menu-btn:active{ transform:translateY(8px); box-shadow:none; }
        .agb-menu-green{ background:#7ba041; }
        .agb-menu-green:hover{ background:#8cc446; }
        .agb-menu-brown{ background:#a67c52; }
        .agb-menu-brown:hover{ background:#b88c60; }
        .agb-menu-red  { background:#d94838; }
        .agb-menu-red:hover  { background:#ed5a49; }
        @keyframes agbHeroJump{
            0%,20%,100%{ transform:translateY(0); }
            45%,55%    { transform:translateY(-70px); }
            75%        { transform:translateY(0); }
        }
        #agb-hero-bounce{ animation:agbHeroJump 1.6s cubic-bezier(.25,.46,.45,.94) infinite; }
        #agb-hero-bounce.silhouette canvas{ filter:brightness(0); }
"""

# Find power-chip block and append new CSS after it
pchip_start = src.find(CSS_ANCHOR)
assert pchip_start != -1, "power-chip anchor not found"
pchip_end_anchor = 'letter-spacing:1px; }'
pchip_end = src.find(pchip_end_anchor, pchip_start)
assert pchip_end != -1
pchip_end += len(pchip_end_anchor)
src = src[:pchip_end] + NEW_CSS + src[pchip_end:]
print('Step 1 done: CSS inserted')

# ── 2. REPLACE titleHTML block ────────────────────────────────────────────────
TITLE_START_ANCHOR = 'const titleHTML=`'
TITLE_END_ANCHOR   = 'document.body.appendChild(titleOv);'

NEW_TITLE = f"""/* ---- TITLE SCREEN ---- */
        const titleScreen = document.createElement('div');
        titleScreen.id = 'agb-title-screen';
        titleScreen.innerHTML = `
          <img class="agb-title-skyline" src="{SKYLINE}" alt="" />
          <div class="agb-cloud agb-cloud-a" style="left:-20%;">
            <div class="agb-cloud-body" style="width:256px;height:96px;">
              <div class="agb-cloud-puff" style="width:128px;height:128px;top:-48px;left:40px;"></div>
              <div class="agb-cloud-puff" style="width:96px;height:96px;top:-32px;right:48px;"></div>
            </div>
          </div>
          <div class="agb-cloud agb-cloud-b" style="right:-20%;opacity:.75;">
            <div class="agb-cloud-body" style="width:192px;height:80px;">
              <div class="agb-cloud-puff" style="width:96px;height:96px;top:-40px;left:32px;"></div>
            </div>
          </div>
          <div style="position:relative;z-index:10;width:100%;max-width:1200px;display:flex;align-items:center;justify-content:space-between;padding:0 40px;height:100%;">
            <div style="display:flex;flex-direction:column;align-items:flex-start;gap:28px;">
              <div style="transform:rotate(-2deg) scale(1.05);margin-left:28px;margin-bottom:8px;">
                <h1 id="agb-logo-main">AWAY GAME</h1>
                <div><span id="agb-logo-sub">BRAWLER</span></div>
              </div>
              <div style="display:flex;flex-direction:column;gap:18px;margin-left:44px;">
                <button class="agb-menu-btn agb-menu-green" id="agb-play">PLAY</button>
                <button class="agb-menu-btn agb-menu-brown" id="agb-settings-btn">SETTINGS</button>
                <button class="agb-menu-btn agb-menu-brown">CREDITS</button>
                <button class="agb-menu-btn agb-menu-red" id="agb-quit-btn">QUIT</button>
              </div>
            </div>
            <div style="position:relative;width:320px;height:320px;margin-right:80px;margin-top:100px;display:flex;align-items:flex-end;justify-content:center;">
              <div id="agb-hero-bounce" style="display:flex;flex-direction:column;align-items:center;">
                <canvas id="agb-title-sprite" width="192" height="192" style="display:block;image-rendering:pixelated;"></canvas>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(titleScreen);"""

i_start = src.find(TITLE_START_ANCHOR)
i_end   = src.find(TITLE_END_ANCHOR, i_start) + len(TITLE_END_ANCHOR)
assert i_start != -1 and i_end > len(TITLE_END_ANCHOR)
src = src[:i_start] + NEW_TITLE + src[i_end:]
print('Step 2 done: title HTML replaced')

# ── 3. REMOVE buildSkinRow() function definition ──────────────────────────────
BSR_START = '    function buildSkinRow(){'
BSR_END   = '    function startRunFromTitle(){'
i_bsr_start = src.find(BSR_START)
i_bsr_end   = src.find(BSR_END, i_bsr_start)
assert i_bsr_start != -1 and i_bsr_end != -1
src = src[:i_bsr_start] + src[i_bsr_end:]
print('Step 3 done: buildSkinRow removed')

# ── 4. UPDATE startRunFromTitle() ────────────────────────────────────────────
SRT_START = '    function startRunFromTitle(){'
SRT_END   = '    }'  # first closing brace after
i_srt = src.find(SRT_START)
assert i_srt != -1
# find next standalone '    }' after function start
i_srt_end = src.find('\n    }', i_srt) + len('\n    }')
OLD_FUNC = src[i_srt:i_srt_end]
print('  Old startRunFromTitle:', repr(OLD_FUNC[:80]))

NEW_SRT = """    function startRunFromTitle(){
        const bounce = document.getElementById('agb-hero-bounce');
        if(bounce) bounce.classList.add('silhouette');
        setTimeout(()=>{
            const ts = document.getElementById('agb-title-screen');
            if(ts){ ts.classList.add('hidden'); setTimeout(()=>{ ts.style.display='none'; STATE.titleSpriteActive=false; }, 420); }
        }, 900);
        STATE.started = true;
        STATE.wave = 1;
        startWaveObjective();
        showTutorial('attack','J / SPACE for light · K for heavy · combo into a finisher every 3 hits');
    }"""

src = src[:i_srt] + NEW_SRT + src[i_srt_end:]
print('Step 4 done: startRunFromTitle updated')

# ── 5. REMOVE buildSkinRow() calls ───────────────────────────────────────────
# In setTimeout block
src = src.replace(
    '        buildSkinRow();\n    }, 0);',
    '        const quitBtn=document.getElementById(\'agb-quit-btn\');\n        if(quitBtn) quitBtn.onclick=()=>{};\n    }, 0);'
)
src = src.replace(
    '        buildSkinRow();\r\n    }, 0);',
    '        const quitBtn=document.getElementById(\'agb-quit-btn\');\r\n        if(quitBtn) quitBtn.onclick=()=>{};\r\n    }, 0);'
)
# In boot()
src = src.replace('        buildSkinRow();\n        // World origin', '        // World origin')
src = src.replace('        buildSkinRow();\r\n        // World origin', '        // World origin')
print('Step 5 done: buildSkinRow calls removed')

# ── 6. ADD title sprite loop in boot() ───────────────────────────────────────
BOOT_ANCHOR = '        // World origin sits inside the sealed interior'
SPRITE_LOOP = """        // Title sprite animation loop
        STATE.titleSpriteActive = true;
        (function titleSpriteLoop(){
            if(!STATE.titleSpriteActive) return;
            const cv = document.getElementById('agb-title-sprite');
            if(!cv){ requestAnimationFrame(titleSpriteLoop); return; }
            const ctx = cv.getContext('2d');
            const entry = TEX['hero'];
            if(!entry || !entry.texture || !entry.texture.image){ requestAnimationFrame(titleSpriteLoop); return; }
            const img = entry.texture.image;
            const cols = entry.cols;
            const CELL_PX = img.width / cols;
            const FPS = 9, BELT_COL = 16, BELT_LEN = 4;
            const frame = Math.floor(performance.now() / 1000 * FPS) % BELT_LEN;
            ctx.clearRect(0, 0, cv.width, cv.height);
            ctx.drawImage(img, (BELT_COL + frame) * CELL_PX, 0, CELL_PX, CELL_PX, 0, 0, cv.width, cv.height);
            requestAnimationFrame(titleSpriteLoop);
        })();
        """

src = src.replace(BOOT_ANCHOR, SPRITE_LOOP + BOOT_ANCHOR, 1)
if SPRITE_LOOP + BOOT_ANCHOR not in src:
    # try CRLF
    BOOT_ANCHOR2 = BOOT_ANCHOR.replace('\n', '\r\n')
    src = src.replace(BOOT_ANCHOR2, SPRITE_LOOP + BOOT_ANCHOR2, 1)
print('Step 6 done: sprite loop added')

# ── 7. WRITE BACK ─────────────────────────────────────────────────────────────
with open(HTML_PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(src)

new_size = len(src)
print(f'Done. {ORIG_LEN:,} -> {new_size:,} bytes (+{new_size-ORIG_LEN:,})')
