import re, json, base64, io
from PIL import Image
with open('C:/Users/q/Desktop/away_game_brawler.html','r',encoding='utf-8') as f:
    src=f.read()
m = re.search(r'JSON\.parse\("(.+)"\);', src, re.DOTALL)
raw = m.group(1).replace('\\\\','\\').replace('\\"','"')
data = json.loads(raw)
for k,v in data.items():
    b = base64.b64decode(v.split(',',1)[1])
    im = Image.open(io.BytesIO(b))
    print(f'{k}: {im.size}  mode={im.mode}  png_bytes={len(b)}  base64_chars={len(v)}')
