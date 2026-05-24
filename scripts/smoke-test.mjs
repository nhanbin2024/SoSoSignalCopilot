import fs from 'node:fs';
const files=['index.html','styles.css','app.js','api/soso.js','api/ai.js','package.json','vercel.json'];
let ok=true;
for(const f of files){if(!fs.existsSync(f)){console.error('missing',f);ok=false;}}
for(const f of ['package.json','vercel.json']) JSON.parse(fs.readFileSync(f,'utf8'));
for(const f of ['api/soso.js','api/ai.js','app.js']){
  const s=fs.readFileSync(f,'utf8');
  if(f==='api/soso.js' && !s.includes('x-soso-api-key')){console.error('missing api key header'); ok=false;}
  if(s.includes('demo-fallback') || s.includes('DEMO')){console.error('demo fallback found in',f); ok=false;}
}
if(!ok) process.exit(1);
console.log('Smoke test passed: live SoSoValue only, no demo fallback.');
