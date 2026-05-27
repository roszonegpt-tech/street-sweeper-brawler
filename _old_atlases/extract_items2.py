"""
Precise extraction of item sprites from the item-index reference sheets.
Creates items_atlas.png: 8 items × 4 frames, each frame 256×256px (8192×256 total).
"""
import os, base64, io
from PIL import Image

IM1 = 'C:/Users/q/Downloads/ChatGPT Image May 22, 2026, 12_01_17 AM.png'
IM2 = 'C:/Users/q/Downloads/ChatGPT Image May 22, 2026, 12_07_18 AM.png'
OUT = 'C:/Users/q/Desktop/_brawler_atlases/items_atlas.png'

im1 = Image.open(IM1).convert('RGB')
im2 = Image.open(IM2).convert('RGB')

CELL = 256

# ── Item crop definitions: (source_img, x0, y0, x1, y1, name, is_throwable) ──
# Coordinates verified from 4×4 tile inspection
# (src, x0, y0, x1, y1, name, is_throwable, bg_threshold)
ITEMS = [
    (im1, 1022,  5, 1120, 140,  'basketball', True,  240),  # orange basketball
    (im2, 1280, 160, 1365, 256, 'bottle',     True,  252),  # ARTZ soda bottle (green glass needs high threshold)
    (im1, 1239, 10, 1389, 125,  'brick',      True,  240),  # red clay brick
    (im2, 1229, 666, 1517, 722, 'metrocard',  True,  240),  # NYC MetroCard
    (im1,  830, 370,  940, 465, 'coin',       False, 248),  # gold coin (bright highlights need higher threshold)
    (im1, 1155, 345, 1237, 440, 'star',       False, 240),  # blue star pickup
    (im1, 1255, 345, 1337, 440, 'heart',      False, 240),  # red heart pickup
    (im2, 1170, 500, 1455, 645, 'boot',       True,  240),  # Timberland boot
]

def make_transparent(im_rgb, threshold=235):
    """Convert near-white pixels to transparent."""
    rgba = im_rgb.convert('RGBA')
    data = list(rgba.getdata())
    result = []
    for r, g, b, a in data:
        if r > threshold and g > threshold and b > threshold:
            result.append((r, g, b, 0))
        else:
            result.append((r, g, b, 255))
    rgba.putdata(result)
    return rgba

def extract_item(im_rgb, x0, y0, x1, y1, threshold=242):
    """Crop, bg-remove, fit into CELL×CELL with padding."""
    region = im_rgb.crop((x0, y0, x1, y1))
    rgba = make_transparent(region, threshold=threshold)
    bbox = rgba.getbbox()
    if not bbox:
        return Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    content = rgba.crop(bbox)
    pad = 20
    inner = CELL - pad * 2
    content.thumbnail((inner, inner), Image.LANCZOS)
    out = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    ox = (CELL - content.width) // 2
    oy = (CELL - content.height) // 2
    out.paste(content, (ox, oy), content)
    return out

def spin_frames(sprite, n=4):
    return [sprite.rotate(360*i/n, resample=Image.BICUBIC) for i in range(n)]

# Build atlas
N = len(ITEMS)
atlas = Image.new('RGBA', (N * 4 * CELL, CELL), (0, 0, 0, 0))
labels = []

for i, (src, x0, y0, x1, y1, name, throwable, thresh) in enumerate(ITEMS):
    sprite = extract_item(src, x0, y0, x1, y1, thresh)
    frames = spin_frames(sprite) if throwable else [sprite] * 4
    for f, frame in enumerate(frames):
        atlas.paste(frame, ((i * 4 + f) * CELL, 0), frame)
    labels.append(name)
    print(f'  {name}: cols {i*4}–{i*4+3}')

atlas.save(OUT, optimize=True)
size = os.path.getsize(OUT)
print(f'\nSaved {OUT}')
print(f'Size: {size:,} bytes  ({size//1024} KB)')

# Encode to base64 and show JS snippet
with open(OUT, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
print(f'\nBase64 length: {len(b64):,} chars ({len(b64)//1024} KB)')

print(f'''
// ── Add to SPRITE_DATA ───────────────────────────────────
// "items": "data:image/png;base64,{b64[:40]}..."

// ── Add after HERO_ANIMS ─────────────────────────────────
const ITEM_ANIMS = {{''')
for i, lbl in enumerate(labels):
    print(f"    {lbl.ljust(12)}: {{ col:{i*4}, len:4, fps:8 }},")
print('};')
print(f'// Atlas: {N} items × 4 frames = {N*4} cols, 1 row, {CELL}px/cell')
