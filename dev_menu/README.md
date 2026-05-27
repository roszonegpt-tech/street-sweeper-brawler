# dev_menu

A tiny, framework-agnostic dev/debug overlay for browser games. One floating
toggle button, one slide-out panel, a backtick hotkey, and a Sprite Lab that
previews any atlas across 8 facings. No build step, no dependencies, vanilla
DOM. Drop it into any project and wire its buttons to your game's callbacks.

## Drop in

```html
<script type="module">
  import { installDevMenu } from './dev_menu.js';
  installDevMenu({
    sections: [
      { title: 'World', buttons: [
        { label: 'Heal me', onClick: () => game.player.hp = game.player.maxHp },
      ]},
    ],
  });
</script>
```

Press the backtick key (or click the `DEV` button bottom-left) to open the panel.

The JS file injects its own CSS by default. If you'd rather load CSS via
`<link rel="stylesheet" href="dev_menu.css">`, pass `{ skipInjectStyles: true }`.

## Config reference

| field            | type     | notes |
|------------------|----------|-------|
| `hotkey`         | string   | Toggle key. Default `` ` `` (also accepts `~`). |
| `position.side`  | `'left' \| 'right'` | Panel anchor side. Default `'right'`. |
| `position.width` | number   | Panel width in px. Default `330`. |
| `sections`       | Section[]| See below. Built in order. |
| `spriteLab`      | object\|null | Atlas previewer; renders only if provided. |
| `showToast`      | `(msg, ms) => void` | Optional. Falls back to `console.log`. |
| `skipInjectStyles` | bool   | Skip the built-in `<style>` injection. |

### Section

```js
{ title: 'WORLD CHEATS', buttons: [...] }
// or for non-button rows:
{ title: 'TUNING', rows: [
  { type: 'slider', label: 'gravity', min: 0, max: 30, step: 0.1, value: 9.8,
    onChange: v => game.gravity = v },
  { type: 'select', label: 'weather', options: ['sun','rain','snow'],
    onChange: v => game.weather = v },
  { type: 'text', placeholder: 'seed', onChange: v => game.seed = v },
  { type: 'html', html: '<small>tip: hold shift</small>' },
  { type: 'buttons', buttons: [{ label: 'apply', onClick: ... }] },
]}
```

### Button

```js
{ label: 'Heal me', onClick: () => game.player.hp = 100 }

// toggle:true — onClick may return a new label string ("foo: ON"/"foo: OFF")
// or { label, on } and the .on class is updated accordingly.
{ label: 'God mode: OFF', toggle: true,
  onClick: btn => { game.god = !game.god;
                    return 'God mode: ' + (game.god ? 'ON' : 'OFF'); } }
```

### Sprite Lab

```js
spriteLab: {
  getAtlases:    () => Object.keys(game.TEX),
  getAtlasEntry: (name) => game.TEX[name],            // { texture:{image}, cols, rows } or { image, cols, rows }
  getAnimsFor:   (name) => game.HERO_ANIMS,           // { idle:{col,len,fps}, run:{...} }
  loadAtlas:     (name, url) => game.loadAtlas(name, url),  // optional
  extraAtlases:  { rusher: 'path/rusher.png', ... },  // optional preset URLs
  cellPx:        256,                                 // sprite cell size
  facings:       ['S','SE','E','NE','N','NW','W','SW'],  // optional
}
```

To **disable Sprite Lab**, omit the `spriteLab` key (or set it to `null`). It
only renders when `getAtlases`, `getAtlasEntry`, and `getAnimsFor` are all
present.

## Returned handle

```js
const dm = installDevMenu({...});
dm.open(); dm.close(); dm.toggle();
dm.rebuild();        // re-render after live data changes (e.g. new atlas loaded)
dm.panelEl; dm.buttonEl;
dm.destroy();        // remove DOM + listeners
```

Install is idempotent: a second `installDevMenu(...)` call destroys the prior
panel before rebuilding.

## Adding a new row type

Open `dev_menu.js` and add a `case 'mytype':` branch to `renderRow()`. Build
the element, attach listeners, and append it to `row`. Then reference it in
your config as `{ type: 'mytype', ... }`.

## Origin

This library is a clean-room rewrite of the dev/debug menu IIFE living in
`away_game_brawler.html` lines 4220–4463 (the `(function devMenu(){...})()`
block). The brawler version was hard-wired to that game's globals (`STATE`,
`TEX`, `HERO_ANIMS`, `spawnEnemy`, `spawnBoss`, `dropPickup`, etc.); this
version turns every game call into a config-supplied callback so the same
look-and-feel — cyan `#7ee0ff` accent, dark panel, slide-out layout, 8-cell
Sprite Lab — can be reused across projects.
