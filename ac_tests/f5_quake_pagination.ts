const SAMPLE = { features: [
  { id:'a', geometry:{coordinates:[0,0,5]}, properties:{ mag:2.6, place:'x', time:1 } },
  { id:'b', geometry:{coordinates:[0,0,5]}, properties:{ mag:4.0, place:'x', time:1 } },
  { id:'c', geometry:{coordinates:[0,0,5]}, properties:{ mag:5.5, place:'x', time:1 } },
  { id:'d', geometry:{coordinates:[0,0,5]}, properties:{ mag:6.2, place:'x', time:1 } },
  { id:'e', geometry:{coordinates:[0,0,5]}, properties:{ mag:3.1, place:'x', time:1 } },
]};
(globalThis as any).fetch = async () => ({ ok:true, status:200, json: async () => SAMPLE });
import { GET } from './src/app/api/earthquakes/route';
const r = (qs: string) => { const u='http://x/api/earthquakes'+qs; const q:any=new Request(u); q.nextUrl=new URL(u); return q; };
const body = async (qs: string) => { const res = await (GET as any)(r(qs)); return { j: await res.json(), h: res.headers }; };
(async () => {
  const eqs = (o: any) => o.j.earthquakes || [];
  const lim = await body('?limit=2');
  const base = await body('');
  const bad = await body('?limit=abc');
  const top2 = [6.2, 5.5];
  const R: [string, boolean][] = [
    ['AC1 ?limit=2 → at most 2', eqs(lim).length <= 2 && eqs(lim).length > 0],
    ['AC2 capped by strongest first', JSON.stringify(eqs(lim).map((e:any)=>e.magnitude)) === JSON.stringify(top2)],
    ['AC3 absent/invalid → all', eqs(base).length === 5 && eqs(bad).length === 5],
    ['AC4 total == returned length', lim.j.total === eqs(lim).length],
    ['AC5 Cache-Control preserved', !!lim.h.get('Cache-Control')],
  ];
  let p=0; for (const [n,ok] of R){ console.log((ok?'PASS ':'FAIL ')+n); if(ok)p++; }
  console.log('SCORE ' + p + '/5');
})();
