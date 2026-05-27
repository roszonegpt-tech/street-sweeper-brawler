import re, json, base64, io
from PIL import Image

path = 'C:/Users/q/Desktop/away_game_brawler.html'
with open(path,'r',encoding='utf-8',newline='') as f:
    lines = f.readlines()

target = None
for i,l in enumerate(lines):
    if 'SPRITE_DATA = JSON.parse(' in l:
        target = i; break

line = lines[target]
m = re.search(r'JSON\.parse\("(.+)"\);', line)
raw = m.group(1).replace('\\\\','\\').replace('\\"','"')
data = json.loads(raw)

# Recompress only the keys that need it.
TO_RECOMPRESS = ['knicks_heavy', 'knicks_woman']
for k in TO_RECOMPRESS:
    if k not in data: continue
    before = data[k]
    raw_bytes = base64.b64decode(before.split(',',1)[1])
    im = Image.open(io.BytesIO(raw_bytes)).convert('RGBA')
    buf = io.BytesIO()
    im.save(buf, format='PNG', optimize=True, compress_level=9)
    new_bytes = buf.getvalue()
    data[k] = 'data:image/png;base64,' + base64.b64encode(new_bytes).decode()
    print(f'{k}: {len(raw_bytes):,} -> {len(new_bytes):,} bytes ({im.size})')

# Re-serialize
json_str = json.dumps(data)
escaped = json_str.replace('\\','\\\\').replace('"','\\"')
new_line = '    const SPRITE_DATA = JSON.parse("' + escaped + '");\n'
lines[target] = new_line

with open(path,'w',encoding='utf-8',newline='') as f:
    f.writelines(lines)
print('rewritten; new SPRITE_DATA line length:', len(new_line))
