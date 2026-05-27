const fs=require('fs');
const c=fs.readFileSync('C:/Users/q/Desktop/away_game_brawler.html','utf8');
const lines=c.split('\n');
console.log('total file size:', c.length);
let idx = -1;
lines.forEach((l,i)=>{ if(l.includes('SPRITE_DATA = JSON.parse(')) idx=i; });
console.log('SPRITE_DATA line:', idx+1, 'length:', lines[idx].length);
// per-line top lengths
const tops=lines.map((l,i)=>[l.length,i+1]).sort((a,b)=>b[0]-a[0]).slice(0,5);
console.log('top lines:'); tops.forEach(([n,i])=>console.log(' ',n,i));
const line=lines[idx];
const m = line.match(/JSON\.parse\("(.+)"\);/);
if(!m){console.log('no match'); process.exit();}
const raw = m[1].replace(/\\\\/g,'\\').replace(/\\"/g,'"');
try{
  const o=JSON.parse(raw);
  console.log('keys:', Object.keys(o));
  for(const [k,v] of Object.entries(o)) console.log(' ',k,'len=',v.length);
}catch(e){ console.log('parse err:',e.message); }
