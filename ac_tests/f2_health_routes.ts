import { GET } from './src/app/api/health/route';
(async () => {
  let j: any, threw = false;
  try { const res = await (GET as any)((() => { const u='http://x/api/health'; const q:any=new Request(u); q.nextUrl=new URL(u); return q; })()); j = await res.json(); }
  catch { threw = true; }
  const eps: string[] = (j && j.endpoints) || [];
  const R: [string, boolean][] = [
    ['AC1 endpoints derived (has many, not the 8 hardcoded)', Array.isArray(eps) && eps.length > 10],
    ['AC2 includes /api/cctv and /api/osint/phone', eps.includes('/api/cctv') && eps.includes('/api/osint/phone')],
    ['AC3 nested full paths present', eps.some(e => e.startsWith('/api/osint/'))],
    ['AC4 returns 200, never throws', !threw && !!j],
    ['AC5 each endpoint is a /api/ string', eps.length > 0 && eps.every(e => typeof e === 'string' && e.startsWith('/api/'))],
  ];
  let p=0; for (const [n,ok] of R){ console.log((ok?'PASS ':'FAIL ')+n); if(ok)p++; }
  console.log('SCORE ' + p + '/5');
})();
