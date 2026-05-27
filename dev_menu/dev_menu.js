// dev_menu.js — drop-in dev/debug overlay for browser games.
// Framework-agnostic. No deps. ES module + UMD-style fallback (attaches to window.DevMenu).
//
// Extracted/refactored from away_game_brawler.html lines 4220-4463
// (the `(function devMenu(){...})()` IIFE). The original was hard-wired
// to the brawler's globals (STATE, TEX, spawnEnemy, HERO_ANIMS, ...);
// this version turns every game-specific call into a config-supplied
// callback so it can be reused across projects.
//
// Public API:
//   import { installDevMenu } from './dev_menu.js';
//   const dm = installDevMenu({ sections: [...], spriteLab: {...} });
//   dm.open(); dm.close(); dm.toggle(); dm.rebuild();
//   dm.panelEl; dm.buttonEl; dm.destroy();

const DEFAULT_CSS = `
#dev-btn{position:fixed;left:10px;bottom:10px;z-index:9998;font:700 11px system-ui;
    background:#1b1b22;color:#7ee0ff;border:1px solid #7ee0ff;border-radius:6px;
    padding:5px 9px;cursor:pointer;opacity:.6}
#dev-btn:hover{opacity:1}
#dev-panel{position:fixed;top:0;width:330px;max-height:100vh;overflow-y:auto;
    z-index:9999;background:rgba(16,16,22,.96);color:#e8e8ee;font:12px/1.35 system-ui;
    padding:10px 12px 40px;display:none;box-shadow:-6px 0 24px rgba(0,0,0,.5)}
#dev-panel.dev-right{right:0;border-left:2px solid #7ee0ff}
#dev-panel.dev-left{left:0;border-right:2px solid #7ee0ff;box-shadow:6px 0 24px rgba(0,0,0,.5)}
#dev-panel.show{display:block}
#dev-panel h3{margin:12px 0 5px;font-size:12px;color:#7ee0ff;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #333;padding-bottom:3px}
#dev-panel h3:first-child{margin-top:0}
#dev-panel button{background:#262631;color:#e8e8ee;border:1px solid #444;border-radius:5px;
    padding:5px 7px;margin:2px 2px 0 0;cursor:pointer;font:600 11px system-ui}
#dev-panel button:hover{background:#34343f;border-color:#7ee0ff}
#dev-panel button.on{background:#1d5e2e;border-color:#5fd07a;color:#bff5c8}
#dev-panel select,#dev-panel input[type=text],#dev-panel input[type=number]{
    background:#1b1b22;color:#e8e8ee;border:1px solid #444;border-radius:5px;
    padding:4px;font:11px system-ui;width:100%;margin:2px 0}
#dev-panel input[type=range]{width:100%}
#dev-panel label{display:block;color:#aaa;font-size:10px;margin-top:4px;text-transform:uppercase;letter-spacing:.04em}
#dev-panel .row{display:flex;gap:4px;align-items:center;flex-wrap:wrap}
#dev-lab-dirs{display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-top:6px}
#dev-lab-dirs canvas{width:100%;background:#0c0c10;border:1px solid #333;border-radius:4px;image-rendering:pixelated}
#dev-lab-dirs .dl{position:relative}
#dev-lab-dirs .dl span{position:absolute;top:1px;left:3px;font:700 9px system-ui;color:#7ee0ff;text-shadow:0 0 3px #000}
#dev-hint{color:#888;font-size:10px;margin-top:8px}
`;

let _liveHandle = null; // for idempotent install

export function installDevMenu(config = {}) {
    // Idempotent: tear down any prior install before rebuilding.
    if (_liveHandle) {
        try { _liveHandle.destroy(); } catch (_) {}
        _liveHandle = null;
    }

    const cfg = {
        hotkey: '`',
        position: { side: 'right', width: 330 },
        sections: [],
        spriteLab: null,
        showToast: null,
        styleId: 'dev-menu-styles',
        ...config,
    };
    cfg.position = { side: 'right', width: 330, ...(config.position || {}) };

    const toast = (msg, ms) => {
        if (typeof cfg.showToast === 'function') return cfg.showToast(msg, ms);
        if (typeof console !== 'undefined') console.log('[DEV]', msg);
    };

    // ---- styles (skip if a host already supplied them externally) ----
    let styleEl = null;
    if (!document.getElementById(cfg.styleId) && !cfg.skipInjectStyles) {
        styleEl = document.createElement('style');
        styleEl.id = cfg.styleId;
        styleEl.textContent = DEFAULT_CSS;
        document.head.appendChild(styleEl);
    }

    // ---- DOM scaffolding ----
    const btn = document.createElement('div');
    btn.id = 'dev-btn';
    btn.textContent = `DEV ${cfg.hotkey} `;
    document.body.appendChild(btn);

    const panel = document.createElement('div');
    panel.id = 'dev-panel';
    panel.classList.add(cfg.position.side === 'left' ? 'dev-left' : 'dev-right');
    if (cfg.position.width) panel.style.width = cfg.position.width + 'px';
    document.body.appendChild(panel);

    // ---- Sprite Lab state ----
    let labRAF = null;
    let labStart = 0;
    let labAtlasSel = null;
    let labAnimSel = null;
    const FACING_DEFAULTS = ['S','SE','E','NE','N','NW','W','SW'];

    // ---- row renderers ----
    function renderButton(btnSpec) {
        const el = document.createElement('button');
        el.textContent = btnSpec.label;
        if (btnSpec.title) el.title = btnSpec.title;
        if (btnSpec.toggle && btnSpec.initialOn) el.classList.add('on');
        el.addEventListener('click', () => {
            try {
                const ret = btnSpec.onClick && btnSpec.onClick(el);
                if (btnSpec.toggle) {
                    // If onClick returns a string, that's the new label.
                    // The .on class toggles based on whether the new label contains "ON"
                    // OR an explicit { label, on } object.
                    if (ret && typeof ret === 'object' && 'on' in ret) {
                        if ('label' in ret) el.textContent = ret.label;
                        el.classList.toggle('on', !!ret.on);
                    } else if (typeof ret === 'string') {
                        el.textContent = ret;
                        el.classList.toggle('on', /\bON\b/i.test(ret));
                    } else {
                        el.classList.toggle('on');
                    }
                }
            } catch (err) {
                console.error('[DevMenu] button onClick error:', err);
            }
        });
        return el;
    }

    function renderRow(rowSpec) {
        const row = document.createElement('div');
        row.className = 'row';
        if (Array.isArray(rowSpec)) {
            // shorthand: array of buttons
            rowSpec.forEach(b => row.appendChild(renderButton(b)));
            return row;
        }
        switch (rowSpec.type) {
            case 'buttons':
            case undefined: {
                (rowSpec.buttons || []).forEach(b => row.appendChild(renderButton(b)));
                break;
            }
            case 'slider': {
                if (rowSpec.label) {
                    const lab = document.createElement('label');
                    lab.textContent = rowSpec.label;
                    row.appendChild(lab);
                }
                const inp = document.createElement('input');
                inp.type = 'range';
                if (rowSpec.min != null) inp.min = rowSpec.min;
                if (rowSpec.max != null) inp.max = rowSpec.max;
                if (rowSpec.step != null) inp.step = rowSpec.step;
                if (rowSpec.value != null) inp.value = rowSpec.value;
                inp.addEventListener('input', () => rowSpec.onChange && rowSpec.onChange(+inp.value, inp));
                row.appendChild(inp);
                break;
            }
            case 'select': {
                if (rowSpec.label) {
                    const lab = document.createElement('label');
                    lab.textContent = rowSpec.label;
                    row.appendChild(lab);
                }
                const sel = document.createElement('select');
                (rowSpec.options || []).forEach(opt => {
                    const o = document.createElement('option');
                    if (typeof opt === 'string') { o.value = opt; o.textContent = opt; }
                    else { o.value = opt.value; o.textContent = opt.label ?? opt.value; }
                    sel.appendChild(o);
                });
                if (rowSpec.value != null) sel.value = rowSpec.value;
                sel.addEventListener('change', () => rowSpec.onChange && rowSpec.onChange(sel.value, sel));
                row.appendChild(sel);
                break;
            }
            case 'text': {
                const inp = document.createElement('input');
                inp.type = 'text';
                if (rowSpec.placeholder) inp.placeholder = rowSpec.placeholder;
                if (rowSpec.value) inp.value = rowSpec.value;
                inp.addEventListener('change', () => rowSpec.onChange && rowSpec.onChange(inp.value, inp));
                row.appendChild(inp);
                break;
            }
            case 'html': {
                if (rowSpec.html != null) row.innerHTML = rowSpec.html;
                else if (rowSpec.element) row.appendChild(rowSpec.element);
                break;
            }
            default:
                console.warn('[DevMenu] unknown row type:', rowSpec.type);
        }
        return row;
    }

    function renderSection(section) {
        const h = document.createElement('h3');
        h.textContent = section.title || '';
        panel.appendChild(h);
        // section.rows is the canonical form; section.buttons is a shorthand for a single row of buttons.
        const rows = section.rows
            || (section.buttons ? [{ type: 'buttons', buttons: section.buttons }] : []);
        rows.forEach(r => panel.appendChild(renderRow(r)));
    }

    // ---- Sprite Lab ----
    function renderSpriteLab() {
        const sl = cfg.spriteLab;
        if (!sl || typeof sl.getAtlases !== 'function' || typeof sl.getAtlasEntry !== 'function'
            || typeof sl.getAnimsFor !== 'function') return;

        const h = document.createElement('h3');
        h.textContent = 'Sprite Lab';
        panel.appendChild(h);

        const atlases = sl.getAtlases() || [];

        const r1 = document.createElement('div'); r1.className = 'row';
        labAtlasSel = document.createElement('select');
        labAtlasSel.id = 'dev-lab-atlas';
        labAtlasSel.innerHTML = atlases.map(a => `<option>${a}</option>`).join('');
        r1.appendChild(labAtlasSel);
        panel.appendChild(r1);

        const r2 = document.createElement('div'); r2.className = 'row';
        labAnimSel = document.createElement('select');
        labAnimSel.id = 'dev-lab-anim';
        r2.appendChild(labAnimSel);
        panel.appendChild(r2);

        const r3 = document.createElement('div'); r3.className = 'row';
        if (sl.extraAtlases && Object.keys(sl.extraAtlases).length && typeof sl.loadAtlas === 'function') {
            const loadAllBtn = document.createElement('button');
            loadAllBtn.textContent = 'Load all extra atlases';
            loadAllBtn.addEventListener('click', () => {
                const known = new Set(sl.getAtlases() || []);
                const tasks = Object.entries(sl.extraAtlases)
                    .filter(([n]) => !known.has(n))
                    .map(([n, u]) => Promise.resolve(sl.loadAtlas(n, u)));
                Promise.all(tasks).then(() => { rebuild(); toast('DEV: extra atlases loaded', 1400); });
            });
            r3.appendChild(loadAllBtn);
        }
        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = 'Refresh list';
        refreshBtn.addEventListener('click', () => rebuild());
        r3.appendChild(refreshBtn);
        panel.appendChild(r3);

        if (typeof sl.loadAtlas === 'function') {
            const r4 = document.createElement('div'); r4.className = 'row'; r4.style.marginTop = '4px';
            const urlInp = document.createElement('input');
            urlInp.type = 'text'; urlInp.id = 'dev-lab-url';
            urlInp.placeholder = 'custom atlas path';
            r4.appendChild(urlInp);
            panel.appendChild(r4);

            const r5 = document.createElement('div'); r5.className = 'row';
            const nameInp = document.createElement('input');
            nameInp.type = 'text'; nameInp.id = 'dev-lab-name';
            nameInp.placeholder = 'name'; nameInp.style.width = '90px';
            r5.appendChild(nameInp);
            const loadBtn = document.createElement('button');
            loadBtn.textContent = 'Load atlas';
            loadBtn.addEventListener('click', () => {
                const url = urlInp.value.trim();
                const nm = nameInp.value.trim() || ('custom' + (sl.getAtlases() || []).length);
                if (!url) return;
                Promise.resolve(sl.loadAtlas(nm, url)).then(() => {
                    rebuild(); toast('DEV: loaded ' + nm, 1400);
                });
            });
            r5.appendChild(loadBtn);
            panel.appendChild(r5);
        }

        const facings = (sl.facings && sl.facings.length) ? sl.facings : FACING_DEFAULTS;
        const dirs = document.createElement('div'); dirs.id = 'dev-lab-dirs';
        dirs.innerHTML = facings.map((d, i) =>
            `<div class="dl"><span>${d}</span><canvas data-dir="${i}" width="96" height="96"></canvas></div>`
        ).join('');
        panel.appendChild(dirs);

        function fillAnims() {
            const m = sl.getAnimsFor(labAtlasSel.value) || {};
            labAnimSel.innerHTML = Object.keys(m).map(k => `<option>${k}</option>`).join('')
                + '<option value="__all">(every column)</option>';
        }
        fillAnims();
        labAtlasSel.onchange = fillAnims;

        const cellPx = sl.cellPx || 256;
        function draw() {
            const at = sl.getAtlasEntry(labAtlasSel.value);
            if (!at) { labRAF = requestAnimationFrame(draw); return; }
            // accept { texture: { image }, cols, rows } OR { image, cols, rows }
            const img = at.image || (at.texture && at.texture.image);
            const cols = at.cols || 1;
            const rows = at.rows || facings.length;
            const animName = labAnimSel.value;
            const t = (performance.now() - labStart) / 1000;
            panel.querySelectorAll('#dev-lab-dirs canvas').forEach(cv => {
                const dir = Math.min(rows - 1, +cv.dataset.dir);
                const ctx = cv.getContext('2d');
                ctx.imageSmoothingEnabled = false;
                ctx.clearRect(0, 0, cv.width, cv.height);
                let col, fps;
                if (animName === '__all') { fps = 8; col = Math.floor(t * fps) % cols; }
                else {
                    const a = (sl.getAnimsFor(labAtlasSel.value) || {})[animName];
                    if (!a) { labRAF = requestAnimationFrame(draw); return; }
                    fps = a.fps || 8;
                    const f = Math.floor(t * fps) % a.len;
                    col = a.col + f;
                }
                if (img && img.complete !== false) {
                    try {
                        ctx.drawImage(img, col * cellPx, dir * cellPx, cellPx, cellPx,
                                      0, 0, cv.width, cv.height);
                    } catch (_) { /* image may not be decodable yet */ }
                }
            });
            labRAF = requestAnimationFrame(draw);
        }
        if (labRAF) cancelAnimationFrame(labRAF);
        labStart = performance.now();
        draw();
    }

    // ---- build / rebuild ----
    function rebuild() {
        if (labRAF) { cancelAnimationFrame(labRAF); labRAF = null; }
        panel.innerHTML = '';
        (cfg.sections || []).forEach(renderSection);
        renderSpriteLab();
        const hint = document.createElement('div');
        hint.id = 'dev-hint';
        hint.textContent = `Hotkey (${cfg.hotkey}) toggles this panel.`;
        panel.appendChild(hint);
    }

    function open()  { rebuild(); panel.classList.add('show'); }
    function close() {
        panel.classList.remove('show');
        if (labRAF) { cancelAnimationFrame(labRAF); labRAF = null; }
    }
    function toggle(force) {
        const show = force === undefined ? !panel.classList.contains('show') : !!force;
        show ? open() : close();
    }

    btn.addEventListener('click', () => toggle());

    function onKey(e) {
        if (e.key !== cfg.hotkey && !(cfg.hotkey === '`' && e.key === '~')) return;
        if (/input|textarea|select/i.test((e.target && e.target.tagName) || '')) return;
        e.preventDefault();
        toggle();
    }
    addEventListener('keydown', onKey);

    function destroy() {
        if (labRAF) { cancelAnimationFrame(labRAF); labRAF = null; }
        removeEventListener('keydown', onKey);
        btn.remove();
        panel.remove();
        // leave styleEl in place — cheap, and other instances may rely on it.
        if (_liveHandle && _liveHandle._panel === panel) _liveHandle = null;
    }

    const handle = {
        open, close, toggle, rebuild, destroy,
        panelEl: panel, buttonEl: btn,
        _panel: panel,
    };
    _liveHandle = handle;
    return handle;
}

// UMD-ish convenience: also expose on window for non-module hosts.
if (typeof window !== 'undefined') {
    window.DevMenu = window.DevMenu || { installDevMenu };
}
