import re, json, sys

path='C:/Users/q/Desktop/away_game_brawler.html'
with open(path,'r',encoding='utf-8',newline='') as f:
    lines=f.readlines()

# Find the SPRITE_DATA line (the long JSON.parse line)
target = None
for i,line in enumerate(lines):
    if 'SPRITE_DATA = JSON.parse(' in line:
        target = i
        break
if target is None:
    print('SPRITE_DATA line not found'); sys.exit(1)

line = lines[target]
print('found on line', target+1, 'length', len(line))

# Extract the JSON string content (between JSON.parse(" ... ");)
m = re.search(r'JSON\.parse\("(.*)"\);', line, re.DOTALL)
if not m:
    print('regex failed'); sys.exit(1)

inner = m.group(1)
# unescape JS string literal: \\ -> \, \" -> "
raw = inner.replace('\\\\','\\').replace('\\"','"')
data = json.loads(raw)
print('keys before:', list(data.keys()), {k: len(v) for k,v in data.items()})

if 'knicks' in data:
    del data['knicks']
    print('removed "knicks"')
else:
    print('no "knicks" key present — nothing to do'); sys.exit(0)

# Re-serialize and escape exactly like the original
json_str = json.dumps(data)
escaped = json_str.replace('\\','\\\\').replace('"','\\"')
new_line = '    const SPRITE_DATA = JSON.parse("' + escaped + '");\n'
lines[target] = new_line
print('new line length:', len(new_line))

with open(path,'w',encoding='utf-8',newline='') as f:
    f.writelines(lines)
print('written')
