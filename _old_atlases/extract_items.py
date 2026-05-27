"""
Extract individual items from the item reference images.
Creates a sprite sheet: items_atlas.png
Each item gets a 256×256 cell, 4 frames (0°/90°/180°/270° rotation for throwables,
or 4 identical frames for static pickups).
Layout: 8 items wide × 1 row = 2048×256 strip
"""
import os, math, io, base64
from PIL import Image, ImageOps, ImageFilter

IMG1 = 'C:/Users/q/Downloads/ChatGPT Image May 22, 2026, 12_01_17 AM.png'
IMG2 = 'C:/Users/q/Downloads/ChatGPT Image May 22, 2026, 12_07_18 AM.png'
OUT  = 'C:/Users/q/Desktop/_brawler_atlases/items_atlas.png'

im1 = Image.open(IMG1).convert('RGBA')
im2 = Image.open(IMG2).convert('RGBA')

W1, H1 = im1.size  # 1535 × 1024
W2, H2 = im2.size  # 1536 × 1024

# ── Manually identified crop boxes (x0, y0, x1, y1) from the reference sheets ──
# Image 1: right half contains items/pickups
# Grid is roughly 4 cols × ~5 rows on the right side (x > ~760)
# Row height ~200px, each item cluster ~190×190px

# From visual inspection:
CROPS = [
    # (image_obj, x0, y0, x1, y1, label, is_throwable)
    (im1,  780,   0, 980, 200, 'basketball', True),   # orange basketball
    (im1,  990,   0,1180, 200, 'bottle',     True),   # glass bottle
    (im1, 1180,   0,1370, 200, 'brick',      True),   # brick block
    (im1, 1370,   0,1535, 200, 'soda_box',   False),  # Sunny's soda
    (im1,  780, 200, 980, 420, 'coin',       False),  # gold coin
    (im1,  980, 200,1180, 420, 'star',       False),  # star pickup
    (im1, 1180, 200,1370, 420, 'heart',      False),  # heart (but visible in row 3)
    (im2,  780, 200, 980, 400, 'boot',       True),   # Timberland boot
]

CELL = 256  # output cell size

def crop_item(im, x0, y0, x1, y1):
    """Crop region, auto-trim whitespace, resize to CELL×CELL with padding."""
    region = im.crop((x0, y0, x1, y1)).convert('RGBA')
    # Build alpha mask from brightness — near-white becomes transparent
    r, g, b, a = region.split()
    # mask = 0 (transparent) where all of R,G,B > 235
    import struct
    pixels_r = list(r.getdata())
    pixels_g = list(g.getdata())
    pixels_b = list(b.getdata())
    mask_data = bytes([0 if (pixels_r[i] > 235 and pixels_g[i] > 235 and pixels_b[i] > 235) else 255
                       for i in range(len(pixels_r))])
    mask = Image.frombytes('L', region.size, mask_data)
    region.putalpha(mask)
    # Crop to content bounding box
    bbox = region.getbbox()
    if not bbox:
        return Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    cropped = region.crop(bbox)
    # Fit into CELL×CELL with 16px padding
    pad = 24
    inner = CELL - pad * 2
    cropped.thumbnail((inner, inner), Image.LANCZOS)
    out = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    x_off = (CELL - cropped.width) // 2
    y_off = (CELL - cropped.height) // 2
    out.paste(cropped, (x_off, y_off), cropped)
    return out

def make_spin_frames(sprite, n=4):
    """Return n frames: rotate 0°, 90°, 180°, 270° for throwable spin."""
    frames = []
    for i in range(n):
        angle = 360 * i / n
        rotated = sprite.rotate(angle, resample=Image.BICUBIC, expand=False)
        frames.append(rotated)
    return frames

# Build atlas: COLS items × 4 frames wide, 1 row tall
ITEMS = CROPS
N_ITEMS = len(ITEMS)
FRAMES = 4
atlas_w = N_ITEMS * FRAMES * CELL
atlas_h = CELL
atlas = Image.new('RGBA', (atlas_w, atlas_h), (0, 0, 0, 0))

labels = []
for col_i, (im_src, x0, y0, x1, y1, label, is_throw) in enumerate(ITEMS):
    sprite = crop_item(im_src, x0, y0, x1, y1)
    if is_throw:
        frames = make_spin_frames(sprite, 4)
    else:
        frames = [sprite] * 4   # static pickup: same frame 4 times
    for f_i, frame in enumerate(frames):
        atlas_x = (col_i * FRAMES + f_i) * CELL
        atlas.paste(frame, (atlas_x, 0), frame)
    labels.append(label)
    print(f'  {label}: col {col_i}, frames {col_i*FRAMES}..{col_i*FRAMES+3}')

atlas.save(OUT, optimize=True)
print(f'\nSaved: {OUT}')
print(f'Atlas size: {atlas.size}  ({N_ITEMS} items × 4 frames)')
print(f'File size: {os.path.getsize(OUT):,} bytes')
print(f'\nItem order: {labels}')
print(f'\nJS constant for game:')
print(f'const ITEM_ANIMS = {{')
for i, lbl in enumerate(labels):
    print(f"    {lbl}: {{ col:{i*4}, len:4, fps:8 }},")
print(f'}};')
