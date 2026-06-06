import { GET } from './src/app/api/live-news/route';
function req(qs: string) { const u='http://x/api/live-news'+qs; const q:any=new Request(u); q.nextUrl=new URL(u); return q; }
async function body(qs: string) { const r = await (GET as any)(req(qs)); return await r.json(); }
(async () => {
  const all = await body('');
  const us = await body('?country=US');
  const fin = await body('?category=finance');
  const comb = await body('?country=US&category=finance');
  const lc = await body('?country=us');
  const R = [
    ['AC1 country=US → only US', us.feeds.length > 0 && us.feeds.every((f: any) => f.country === 'US')],
    ['AC2 category=finance → only finance', fin.feeds.length > 0 && fin.feeds.every((f: any) => f.category === 'finance')],
    ['AC3 combined AND', comb.feeds.every((f: any) => f.country === 'US' && f.category === 'finance')],
    ['AC4 case-insensitive (?country=us == US)', lc.feeds.length === us.feeds.length && lc.feeds.length > 0],
    ['AC5 total==filtered length & no-params=full', us.total === us.feeds.length && all.total === all.feeds.length],
  ];
  let pass = 0;
  for (const [n, ok] of R) { console.log((ok ? 'PASS ' : 'FAIL ') + n); if (ok) pass++; }
  console.log('SCORE ' + pass + '/5');
})();
