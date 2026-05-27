"""Smart atlas combiner for Away Game Brawler.

For each character's per-anim sheets, this script:
1. Chroma-keys the hot-pink background to transparent.
2. Detects each row band by finding horizontal "rivers" of fully-transparent pixels.
3. Within each row, detects each column band the same way.
4. For each detected cell, finds the alpha bbox, downscales to fit cleanly inside
   a clean 256x256 output cell with the figure bottom-aligned.
5. Concatenates all anim panels horizontally into one merged atlas PNG.

Output dimensions are always (n_anims * 4) cols x N rows of 256x256, where N is
the row count of the FIRST input sheet (capped at 8). The brawler engine reads
rows from image height at load.
"""
import os
from PIL import Image

# Paths are relative to the script (the repo it lives in). Lets the script keep
# working after the repo gets moved or cloned somewhere else.
_HERE = os.path.dirname(os.path.abspath(__file__))
IN_DIR  = os.path.join(_HERE, 'away_game_brawler_assets', 'New Characters Input')
OUT_DIR = os.path.join(_HERE, 'away_game_brawler_assets', 'character_atlases')
CELL = 256
TARGET_COLS = 4   # each input panel is 4 frames wide (animation frames)
TARGET_ROWS = 8   # engine expects 8 facings (S, SE, E, NE, N, NW, W, SW). When a
                  # source has fewer (e.g. AI drew only 6), cross-row fill copies
                  # the nearest non-empty facing into the missing slots.
PAD = 6           # px padding inside each output cell
ALPHA_THRESH = 16 # pixel counts as content if alpha >= this
# How much of the cell the trimmed figure should fill (height-wise). Anything
# below this gets upscaled. Anything above gets downscaled. Keeps sprite sizes
# uniform across atlases regardless of how big the AI happened to draw them.
TARGET_FILL = 0.86
MAX_UPSCALE = 3.5
# Cells smaller than this fraction of the cell area are treated as scrap and
# replaced by a neighbor — kills the "tiny stray figure" artifacts the user saw
# alongside legit figures.
MIN_BBOX_FILL = 0.04

JOBS = [
    ('celtics_0', [
        'ChatGPT Image May 22, 2026, 11_19_59 PM (1).png',
        'ChatGPT Image May 22, 2026, 11_19_59 PM (2).png',
        'ChatGPT Image May 22, 2026, 11_19_59 PM (3).png',
        'ChatGPT Image May 22, 2026, 11_19_59 PM (5).png',
        'ChatGPT Image May 22, 2026, 11_19_59 PM (6).png',
    ]),
    ('hawks_v2', [
        'ChatGPT Image May 22, 2026, 11_30_04 PM (1).png',
        'ChatGPT Image May 22, 2026, 11_30_04 PM (2).png',
        'ChatGPT Image May 22, 2026, 11_30_04 PM (3).png',
        'ChatGPT Image May 22, 2026, 11_30_04 PM (5).png',
        'ChatGPT Image May 22, 2026, 11_30_04 PM (6).png',
        'ChatGPT Image May 22, 2026, 11_30_04 PM (4).png',
    ]),
    ('heavy_bball', [
        'ChatGPT Image May 22, 2026, 11_30_26 PM (1).png',
        'ChatGPT Image May 22, 2026, 11_30_26 PM (2).png',
        'ChatGPT Image May 22, 2026, 11_30_26 PM (3).png',
        'ChatGPT Image May 22, 2026, 11_30_26 PM (4).png',
        'ChatGPT Image May 22, 2026, 11_30_26 PM (5).png',
    ]),
    ('sixers_21', [
        'ChatGPT Image May 23, 2026, 12_40_04 AM (1).png',
        'ChatGPT Image May 23, 2026, 12_40_04 AM (2).png',
        'ChatGPT Image May 23, 2026, 12_40_05 AM (3).png',
        'ChatGPT Image May 23, 2026, 12_40_05 AM (5).png',
        'ChatGPT Image May 23, 2026, 12_40_06 AM (6).png',
    ]),
    ('fighter_f', [
        'ChatGPT Image May 23, 2026, 01_09_21 AM (1).png',
        'ChatGPT Image May 23, 2026, 01_09_21 AM (2).png',
        'ChatGPT Image May 23, 2026, 01_09_22 AM (4).png',
        'ChatGPT Image May 23, 2026, 01_09_22 AM (5).png',
        'ChatGPT Image May 23, 2026, 01_09_22 AM (6).png',
    ]),
]


def chroma_key(img):
    """Convert hot pink background to alpha=0."""
    img = img.convert('RGBA')
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # hot pink: R high, G low, B medium+, big channel spread
            if r > 180 and g < 60 and b > 90 and (r - g) > 120 and (b - g) > 60:
                px[x, y] = (0, 0, 0, 0)
    return img


def find_bands(mask, axis, gap_thresh=2):
    """Given a 2D bool mask, return list of (start, end) bands along the given axis
    where the perpendicular sum > 0 (content). axis=0 -> row bands, axis=1 -> col bands.
    Used for VERY GAPPY sources (clear background between figures)."""
    w, h = mask.size
    if axis == 0:
        counts = [sum(1 for x in range(w) if mask.getpixel((x, y))) for y in range(h)]
    else:
        counts = [sum(1 for y in range(h) if mask.getpixel((x, y))) for x in range(w)]
    bands = []
    in_band = False
    start = 0
    gap = 0
    for i, c in enumerate(counts):
        if c > gap_thresh:
            if not in_band:
                start = i
                in_band = True
            gap = 0
        else:
            if in_band:
                gap += 1
                if gap > 4:
                    bands.append((start, i - gap))
                    in_band = False
    if in_band:
        bands.append((start, len(counts) - 1))
    return bands


def find_peaks_1d(counts, expected_max, valley_drop=0.45):
    """Generic peak-band detector for tight-packed sources. Returns list of
    (start, end) bands. Used for both rows (axis=0) and columns within a row.
    `expected_max` caps how many bands we look for so we don't over-segment."""
    n = len(counts)
    if not counts or max(counts) == 0:
        return []
    win = max(5, n // 50)
    sm = [0.0] * n
    for i in range(n):
        lo, hi = max(0, i - win // 2), min(n, i + win // 2 + 1)
        sm[i] = sum(counts[lo:hi]) / (hi - lo)
    cm = max(0.5, max(sm) * 0.10)
    i_first = next((i for i, v in enumerate(sm) if v >= cm), 0)
    i_last  = n - 1 - next((i for i, v in enumerate(reversed(sm)) if v >= cm), 0)
    span = i_last - i_first + 1
    valley_win = max(3, span // (expected_max * 6))
    valleys = []
    for i in range(i_first + valley_win, i_last - valley_win + 1):
        v = sm[i]
        is_min = all(sm[i - k] >= v and sm[i + k] >= v for k in range(1, valley_win + 1))
        local_max = max(sm[i - valley_win:i + valley_win + 1])
        if is_min and v <= local_max * valley_drop:
            valleys.append(i)
    # dedup
    if valleys:
        dd = [valleys[0]]
        for v in valleys[1:]:
            if v - dd[-1] > span / (expected_max * 3):
                dd.append(v)
        valleys = dd
    bands = []
    starts = [i_first] + [v + 1 for v in valleys]
    ends   = [v - 1 for v in valleys] + [i_last]
    for s, e in zip(starts, ends):
        if e - s > 6:
            bands.append((s, e))
    return bands


def find_col_bands_in_row(img, row_y0, row_y1, target_cols):
    """For a given row band, detect column bands within it. Tries gap-detect first,
    then peak-find, and finally falls back to equal-width slots."""
    w = img.width
    # count opaque pixels per column within the row strip
    px = img.load()
    counts = []
    for x in range(w):
        c = 0
        for y in range(row_y0, row_y1 + 1):
            if px[x, y][3] >= ALPHA_THRESH:
                c += 1
        counts.append(c)
    # gap detect (need clear 0-pixel gaps)
    bands = []
    in_band = False; start = 0; gap = 0
    for i, c in enumerate(counts):
        if c > 2:
            if not in_band:
                start = i; in_band = True
            gap = 0
        else:
            if in_band:
                gap += 1
                if gap > 6:
                    bands.append((start, i - gap))
                    in_band = False
    if in_band:
        bands.append((start, len(counts) - 1))
    # if gap detect found ~target_cols, use it
    if abs(len(bands) - target_cols) <= 1 and len(bands) >= 2:
        return _normalize_band_count(bands, target_cols)
    # else try peak-find
    peaks = find_peaks_1d(counts, target_cols, valley_drop=0.5)
    if len(peaks) >= 2:
        return _normalize_band_count(peaks, target_cols)
    # final fallback: equal-width slots over the content extent
    nz = [i for i, c in enumerate(counts) if c > 1]
    if not nz:
        return [(int(i * w / target_cols), int((i + 1) * w / target_cols) - 1) for i in range(target_cols)]
    x0, x1 = nz[0], nz[-1]
    step = (x1 - x0 + 1) / target_cols
    return [(int(x0 + i * step), int(x0 + (i + 1) * step) - 1) for i in range(target_cols)]


def _normalize_band_count(bands, target):
    """Land on exactly `target` bands. If source has MORE bands than target,
    SAMPLE (pick evenly-distributed indices) — never merge, which would put two
    figures in one output cell. If source has fewer, split the widest."""
    if len(bands) == target:
        return list(bands)
    if len(bands) > target:
        # Pick `target` evenly-spaced bands. For 6→4 we get indices [0,2,3,5];
        # for 8→4 we get [0,2,5,7]. Always includes endpoints.
        n = len(bands)
        idx = [round(i * (n - 1) / (target - 1)) for i in range(target)]
        # dedup while preserving order (rounding can collide)
        seen, picked = set(), []
        for i in idx:
            if i not in seen:
                seen.add(i); picked.append(i)
        # if dedup dropped some, fill from unused indices nearest the middle
        unused = [i for i in range(n) if i not in seen]
        unused.sort(key=lambda x: abs(x - n // 2))
        while len(picked) < target and unused:
            picked.append(unused.pop(0))
        picked.sort()
        return [bands[i] for i in picked]
    # fewer than target: split the widest bands until we hit target
    bands = list(bands)
    while len(bands) < target:
        widest = max(range(len(bands)), key=lambda i: bands[i][1] - bands[i][0])
        s, e = bands[widest]
        mid = (s + e) // 2
        bands[widest] = (s, mid - 1)
        bands.insert(widest + 1, (mid + 1, e))
    return bands


def find_row_peaks(mask, expected_max_rows=8):
    """For sheets where figures are packed tightly with no clear gaps, find
    rows via PEAKS in the per-row alpha count. Smooth, then pick local maxima
    that are at least min_spacing apart.

    Returns list of (y_start, y_end) bands approximating each row.
    """
    w, h = mask.size
    counts = [sum(1 for x in range(w) if mask.getpixel((x, y))) for y in range(h)]
    if max(counts) == 0:
        return []
    # smooth with a centered moving average
    win = 11
    sm = [0.0] * h
    half = win // 2
    for i in range(h):
        lo, hi = max(0, i - half), min(h, i + half + 1)
        sm[i] = sum(counts[lo:hi]) / (hi - lo)
    # find first/last content row
    content_min = max(0.5, max(sm) * 0.10)
    y_first = next((i for i, v in enumerate(sm) if v >= content_min), 0)
    y_last  = h - 1 - next((i for i, v in enumerate(reversed(sm)) if v >= content_min), 0)
    span = y_last - y_first + 1
    # Local minima (valleys) between rows. Use a sliding window to find dips.
    valleys = []
    valley_win = max(5, span // (expected_max_rows * 6))
    for i in range(y_first + valley_win, y_last - valley_win + 1):
        v = sm[i]
        is_min = all(sm[i - k] >= v and sm[i + k] >= v for k in range(1, valley_win + 1))
        # require a meaningful dip relative to surroundings
        local_max = max(sm[i - valley_win:i + valley_win + 1])
        if is_min and v <= local_max * 0.45:
            valleys.append(i)
    # collapse close valleys (within min_spacing/2)
    if valleys:
        deduped = [valleys[0]]
        for v in valleys[1:]:
            if v - deduped[-1] > span / (expected_max_rows * 3):
                deduped.append(v)
        valleys = deduped
    # build bands: from y_first..valleys[0], between valleys, last valley..y_last
    bands = []
    starts = [y_first] + [v + 1 for v in valleys]
    ends   = [v - 1 for v in valleys] + [y_last]
    for s, e in zip(starts, ends):
        if e - s > 8:
            bands.append((s, e))
    return bands


def alpha_mask(img):
    """Return a 1-bit Image where alpha >= threshold."""
    w, h = img.size
    px = img.load()
    mask = Image.new('1', (w, h), 0)
    mpx = mask.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] >= ALPHA_THRESH:
                mpx[x, y] = 1
    return mask


def find_bbox(img, x0, y0, x1, y1):
    """Find alpha bbox inside the (x0,y0)-(x1,y1) crop. Returns None if empty."""
    px = img.load()
    min_x, min_y, max_x, max_y = x1, y1, x0 - 1, y0 - 1
    for y in range(y0, y1):
        for x in range(x0, x1):
            if px[x, y][3] >= ALPHA_THRESH:
                if x < min_x: min_x = x
                if y < min_y: min_y = y
                if x > max_x: max_x = x
                if y > max_y: max_y = y
    if max_x < x0:
        return None
    return (min_x, min_y, max_x + 1, max_y + 1)


def build_clean_panel(input_img, target_cols=4):
    """Detect grid in input_img, output a clean (target_cols * CELL) x (rows * CELL) PNG.
    Returns (output_image, row_count)."""
    img = chroma_key(input_img)
    mask = alpha_mask(img)
    row_bands = find_bands(mask, 0)
    # If gap-detect found <= 1 row (figures packed tight), fall back to peak-find.
    if len(row_bands) <= 1:
        row_bands = find_row_peaks(mask)
    if not row_bands:
        return Image.new('RGBA', (target_cols * CELL, CELL), (0, 0, 0, 0)), 1

    # Always allocate TARGET_ROWS so short sources get padded later by the
    # cross-row fill pass. The first `len(row_bands)` rows hold detected art;
    # rows beyond that start empty and are filled from neighbors below.
    rows = max(len(row_bands), TARGET_ROWS)
    out = Image.new('RGBA', (target_cols * CELL, rows * CELL), (0, 0, 0, 0))

    for ri, (ry0, ry1) in enumerate(row_bands):
        # Detect columns within this row band so we work with the AI's actual layout
        # (some sources are 4 cols, others 6/7). Then normalize to target_cols by
        # sampling so the output is always a clean 4-frame anim panel.
        col_bands = find_col_bands_in_row(img, ry0, ry1, target_cols)
        # the source row band's pixel area — used to filter out scrap-sized bboxes
        row_band_area = (ry1 - ry0 + 1) * (img.width // max(1, len(col_bands)))
        for ci, (cx0, cx1) in enumerate(col_bands):
            bbox = find_bbox(img, cx0, ry0, cx1 + 1, ry1 + 1)
            if not bbox:
                continue
            bx0, by0, bx1, by1 = bbox
            bw, bh = bx1 - bx0, by1 - by0
            # Skip cells whose content is tiny relative to the source cell area —
            # these are usually overflow scraps from a neighbor figure that crept
            # in past the col-band boundary.
            if (bw * bh) < (row_band_area * MIN_BBOX_FILL):
                continue
            avail_w = CELL - PAD * 2
            avail_h = CELL - PAD * 2
            # Target: figure's HEIGHT fills TARGET_FILL of cell height. Apply uniform
            # scale (preserve aspect), then clamp so we don't overflow horizontally
            # or upscale beyond MAX_UPSCALE (which would blow up tiny artifacts).
            target_h = avail_h * TARGET_FILL
            s = target_h / bh
            if bw * s > avail_w:
                s = avail_w / bw
            s = min(s, MAX_UPSCALE)
            dw, dh = max(1, int(bw * s)), max(1, int(bh * s))
            # output cell origin
            ox = ci * CELL + (CELL - dw) // 2
            # bottom-align (feet on ground)
            oy = ri * CELL + (CELL - PAD - dh)
            crop = img.crop((bx0, by0, bx1, by1))
            if (dw, dh) != (bw, bh):
                # Use BICUBIC for upscaling so we don't get jagged blocky pixels;
                # downscaling stays NEAREST to preserve crisp edges on already-pixel art.
                resample = Image.BICUBIC if s > 1.0 else Image.NEAREST
                crop = crop.resize((dw, dh), resample)
            out.paste(crop, (ox, oy), crop)

    # ---- Hold-frame fill ----
    # If the AI didn't draw a particular frame, the output cell ends up empty
    # and the animation visibly BLINKS when the engine cycles to that frame.
    # Copy the nearest non-empty cell from the same row into the empty slot
    # so the anim shows a held frame instead of a transparent gap.
    out_px = out.load()
    def cell_is_empty(ri, ci):
        x0, y0 = ci * CELL, ri * CELL
        for y in range(y0 + 8, y0 + CELL - 8, 4):
            for x in range(x0 + 8, x0 + CELL - 8, 4):
                if out_px[x, y][3] >= ALPHA_THRESH:
                    return False
        return True
    # ---- pass 1: within-row hold-frame fill (per-frame gap → hold previous) ----
    for ri in range(rows):
        empty = [ci for ci in range(target_cols) if cell_is_empty(ri, ci)]
        filled = [ci for ci in range(target_cols) if ci not in empty]
        if not filled or not empty:
            continue
        for ci in empty:
            nearest = min(filled, key=lambda f: abs(f - ci))
            src_box = (nearest * CELL, ri * CELL, (nearest + 1) * CELL, (ri + 1) * CELL)
            patch = out.crop(src_box)
            out.paste(patch, (ci * CELL, ri * CELL), patch)

    # ---- pass 2: cross-row fallback (entire row empty → borrow from nearest row) ----
    # When the AI completely skipped a facing (common: SW), we'd render invisible
    # for that direction. Copy the whole 4-frame row from the nearest non-empty row.
    row_filled = []
    for ri in range(rows):
        any_filled = any(not cell_is_empty(ri, ci) for ci in range(target_cols))
        row_filled.append(any_filled)
    if any(row_filled):
        for ri in range(rows):
            if row_filled[ri]:
                continue
            # find nearest non-empty row
            nearest = min((r for r, f in enumerate(row_filled) if f), key=lambda r: abs(r - ri))
            src_box = (0, nearest * CELL, target_cols * CELL, (nearest + 1) * CELL)
            patch = out.crop(src_box)
            out.paste(patch, (0, ri * CELL), patch)

    return out, rows


def build_atlas(name, files):
    panels = []
    max_rows = 0
    for fn in files:
        p = os.path.join(IN_DIR, fn)
        if not os.path.exists(p):
            print(f'  MISSING: {fn}')
            continue
        with Image.open(p) as src:
            panel, rows = build_clean_panel(src.copy(), TARGET_COLS)
            panels.append((panel, rows))
            max_rows = max(max_rows, rows)
    if not panels:
        return
    # Pad shorter panels with extra empty rows so all match max_rows.
    out_w = TARGET_COLS * CELL * len(panels)
    out_h = max_rows * CELL
    out = Image.new('RGBA', (out_w, out_h), (0, 0, 0, 0))
    for i, (panel, rows) in enumerate(panels):
        # paste at top — extra empty rows go to the bottom
        out.paste(panel, (i * TARGET_COLS * CELL, 0), panel)
    op = os.path.join(OUT_DIR, name + '.png')
    out.save(op, 'PNG')
    print(f'  wrote {op}  ({out_w}x{out_h}, rows={max_rows})')


def main():
    print('Building clean atlases...')
    for name, files in JOBS:
        print(f'{name}:')
        build_atlas(name, files)


if __name__ == '__main__':
    main()
