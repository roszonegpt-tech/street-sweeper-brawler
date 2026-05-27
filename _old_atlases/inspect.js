const fs=require('fs');
const c=fs.readFileSync('C:/Users/q/Desktop/away_game_brawler.html','utf8');
const lines=c.split('\n');
const line=lines[253];
console.log('starts with:', line.slice(0,150));
console.log('ends with:', line.slice(-100));
console.log('line length:', line.length);
const m=line.match(/JSON\.parse\("(.+)"\);/);
if(!m){ console.log('no JSON match'); process.exit(); }
let s=m[1];
// unescape JS string literal -> get raw JSON
s=s.replace(/\\\\/g,'\\').replace(/\\"/g,'"');
try{
  const o=JSON.parse(s);
  console.log('valid JSON; keys=', Object.keys(o));
  for(const [k,v] of Object.entries(o)){
    console.log(' ',k,'len=',v.length);
  }
}catch(e){
  console.log('INVALID:', e.message);
}
