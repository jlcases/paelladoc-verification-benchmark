// Executable AC check for f3 (server-side TTL cache). Counts fetches + controls the clock.
let fetchCount = 0;
let failNext = false;
(globalThis as any).fetch = async () => {
  fetchCount++;
  if (failNext) throw new Error('upstream down');
  return { ok: true, status: 200, json: async () => ([{ kp_index: '3', time_tag: 't', Kp: 3 }]) };
};
let now = 1_000_000;
const realNow = Date.now.bind(Date);
(Date as any).now = () => now;
import { GET } from './src/app/api/space-weather/route';
const call = async () => { const res = await (GET as any)((() => { const u='http://x/api/space-weather'; const q:any=new Request(u); q.nextUrl=new URL(u); return q; })()); return { j: await res.json(), h: res.headers }; };
(async () => {
  const a = await call();      const c1 = fetchCount;
  const b = await call();      const c2 = fetchCount;          // immediate 2nd call → within TTL
  now += 10 * 60 * 1000;                                       // advance 10 min (past any sane TTL)
  const c = await call();      const c3 = fetchCount;          // → should refetch
  let threw = false;
  failNext = true; now += 10 * 60 * 1000;
  try { await call(); } catch { threw = true; }                // upstream fails after TTL
  const R: [string, boolean][] = [
    ['AC1 in-memory cache (1st call fetched, payload returned)', c1 > 0 && !!a.j],
    ['AC2 within TTL → 2nd call no new fetch', c2 === c1],
    ['AC3 after TTL → refetch happens', c3 > c2],
    ['AC4 Cache-Control header set', !!a.h.get('Cache-Control')],
    ['AC5 upstream failure → no throw', !threw],
  ];
  let p=0; for (const [n,ok] of R){ console.log((ok?'PASS ':'FAIL ')+n); if(ok)p++; }
  console.log('SCORE ' + p + '/5');
  void realNow; void b;
})();
