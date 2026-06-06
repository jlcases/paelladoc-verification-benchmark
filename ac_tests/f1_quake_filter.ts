// Executable AC check for f1 (minMagnitude filter). Mocks USGS fetch with known magnitudes.
const SAMPLE = { features: [
  { id: 'a', geometry: { coordinates: [0,0,5] }, properties: { mag: 2.6, place: 'x', time: 1 } },
  { id: 'b', geometry: { coordinates: [0,0,5] }, properties: { mag: 4.0, place: 'x', time: 1 } },
  { id: 'c', geometry: { coordinates: [0,0,5] }, properties: { mag: 5.5, place: 'x', time: 1 } },
  { id: 'd', geometry: { coordinates: [0,0,5] }, properties: { mag: 6.2, place: 'x', time: 1 } },
  { id: 'e', geometry: { coordinates: [0,0,5] }, properties: { mag: 3.1, place: 'x', time: 1 } },
]};
(globalThis as any).fetch = async () => ({ ok: true, status: 200, json: async () => SAMPLE });
import { GET } from './src/app/api/earthquakes/route';
const r = (qs: string) => { const u='http://x/api/earthquakes'+qs; const q:any=new Request(u); q.nextUrl=new URL(u); return q; };
const body = async (qs: string) => { const res = await (GET as any)(r(qs)); return { j: await res.json(), h: res.headers }; };
(async () => {
  const base = await body('');
  const hi = await body('?minMagnitude=5');
  const bad = await body('?minMagnitude=abc');
  const eqs = (o: any) => o.j.earthquakes || [];
  const R: [string, boolean][] = [
    ['AC1 ?minMagnitude=5 → only mag>=5', eqs(hi).length > 0 && eqs(hi).every((e: any) => e.magnitude >= 5)],
    ['AC2 absent → all returned', eqs(base).length === 5],
    ['AC3 invalid → not empty, no crash (full set)', eqs(bad).length === 5],
    ['AC4 total == returned length', hi.j.total === eqs(hi).length],
    ['AC5 Cache-Control preserved', !!hi.h.get('Cache-Control')],
  ];
  let p = 0; for (const [n, ok] of R) { console.log((ok?'PASS ':'FAIL ')+n); if (ok) p++; }
  console.log('SCORE ' + p + '/5');
})();
