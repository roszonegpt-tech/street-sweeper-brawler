import json, os
src='C:/Users/q/Desktop/away_game_brawler.html'
with open('C:/Users/q/Desktop/_brawler_atlases/sprite_data.json') as f:
    data=json.load(f)
json_str = json.dumps(data)
escaped = json_str.replace('\\', '\\\\').replace('"', '\\"')
new_line = '    const SPRITE_DATA = JSON.parse("' + escaped + '");\n'
print('new line length:', len(new_line))

with open(src,'r',encoding='utf-8',newline='') as f:
    lines=f.readlines()
print('total lines:', len(lines))
print('line 245 head:', lines[244][:80])
print('line 251 head:', lines[250][:80])

lines[244] = new_line
lines[250] = lines[250].replace('const CELL = 40', 'const CELL = 256')
print('new line 251 head:', lines[250][:80])

with open(src,'w',encoding='utf-8',newline='') as f:
    f.writelines(lines)
print('done, file size:', os.path.getsize(src))
