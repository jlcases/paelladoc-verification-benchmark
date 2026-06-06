#!/usr/bin/env python3
"""Independent, blind scorer for v2. Re-score every saved diff by EXECUTION, not by reading it.
For each run: apply the diff to a fresh frozen worktree, import the route, call it with real
Requests (fetch mocked deterministically inside the AC test), assert each acceptance criterion.
The scorer is given NO arm label and NO engine identity beyond the filename it must group by;
it applies the IDENTICAL assertions to every arm. This is what separates treatment from
measurement: nothing scores its own output.

Each AC is pre-tagged genuine|contract in features.json. The headline metric counts only
GENUINE failures (a real correctness bug any competent impl should avoid). Contract failures
(an arbitrary interface the model wasn't told) are reported separately and excluded from the
headline on purpose.

Outputs: exec_scores_v2.json (per-run) + RESULTS.md (aggregates with 95% Wilson CIs + variance).
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
TESTS = HERE / "ac_tests"
_BENCH = os.environ.get("BENCH_REPO")
if not _BENCH:
    raise SystemExit("set BENCH_REPO=/path/to/osiris (the frozen Next.js test repo, at 37c4cc4)")
OSIRIS = Path(_BENCH)
NODE_MODULES = OSIRIS / "node_modules"
FROZEN = "37c4cc4"
WORKDIR = Path("/tmp/score_v2")
FEATURES = {f["id"]: f for f in json.load(open(HERE / "features.json"))}
TEST_FOR = {
    "f1_quake_filter": "f1_quake_filter.ts",
    "f2_health_routes": "f2_health_routes.ts",
    "f3_spaceweather_cache": "f3_spaceweather_cache.ts",
    "f4_news_filter": "f4_news_filter.ts",
    "f5_quake_pagination": "f5_quake_pagination.ts",
}
STEM_RE = re.compile(r"^(?P<fid>f\d_[a-z_]+)__(?P<engine>\w+)__(?P<arm>Bp?|A)__r(?P<run>\d+)$")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Return (p, lo, hi) — point estimate and 95% Wilson interval for k successes in n."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def score_one(diff_path: Path) -> dict | None:
    m = STEM_RE.match(diff_path.stem)
    if not m:
        return None
    fid, engine, arm, run = m["fid"], m["engine"], m["arm"], int(m["run"])
    if fid not in TEST_FOR:
        return None
    ac_types = FEATURES[fid]["ac_types"]
    rec = {"feature": fid, "engine": engine, "arm": arm, "run": run}
    diff_text = diff_path.read_text()
    if not diff_text.strip():
        return {**rec, "status": "empty_diff", "pass_flags": [False] * len(ac_types)}
    wt = WORKDIR / diff_path.stem
    if wt.exists():
        subprocess.run(["git", "-C", str(OSIRIS), "worktree", "remove", "--force", str(wt)],
                       capture_output=True)
        shutil.rmtree(wt, ignore_errors=True)
    subprocess.run(["git", "-C", str(OSIRIS), "worktree", "add", "--detach", str(wt), FROZEN],
                   capture_output=True, check=True)
    # --3way is the most robust (resolves via blob ancestry); fall back to --recount.
    ap = subprocess.run(["git", "-C", str(wt), "apply", "--3way", "--ignore-whitespace",
                         str(diff_path)], capture_output=True, text=True)
    if ap.returncode != 0:
        ap = subprocess.run(["git", "-C", str(wt), "apply", "--ignore-whitespace", "--recount",
                             str(diff_path)], capture_output=True, text=True)
    if ap.returncode != 0:
        _cleanup(wt)
        return {**rec, "status": "apply_failed", "pass_flags": None, "tail": ap.stderr[-300:]}
    subprocess.run(["cp", "-cR", str(NODE_MODULES), str(wt / "node_modules")], check=True)
    shutil.copy(TESTS / TEST_FOR[fid], wt / "ac.ts")
    try:
        proc = subprocess.run(["npx", "tsx", "ac.ts"], cwd=str(wt), capture_output=True,
                              text=True, timeout=120)
        out = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    _cleanup(wt)
    # ordered PASS/FAIL lines, one per AC
    flags = [ln.startswith("PASS") for ln in out.splitlines() if ln.startswith(("PASS", "FAIL"))]
    if len(flags) != len(ac_types):
        return {**rec, "status": "exec_error", "pass_flags": None, "tail": out[-300:]}
    return {**rec, "status": "ok", "pass_flags": flags}


def _cleanup(wt: Path) -> None:
    shutil.rmtree(wt / "node_modules", ignore_errors=True)
    subprocess.run(["git", "-C", str(OSIRIS), "worktree", "remove", "--force", str(wt)],
                   capture_output=True)


def derived(rec: dict) -> dict:
    """Add all_pass, genuine_bug, contract_fail to a scored record."""
    flags = rec.get("pass_flags")
    ac_types = FEATURES[rec["feature"]]["ac_types"]
    if flags is None:  # apply_failed / exec_error → not scorable, leave None
        return {**rec, "all_pass": None, "genuine_bug": None, "contract_fail": None}
    all_pass = all(flags)
    genuine_bug = any((not ok) and t == "genuine" for ok, t in zip(flags, ac_types))
    contract_fail = sum((not ok) and t == "contract" for ok, t in zip(flags, ac_types))
    return {**rec, "all_pass": all_pass, "genuine_bug": genuine_bug, "contract_fail": contract_fail}


def main() -> None:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    diffs = sorted(d for d in RUNS.glob("*.diff") if STEM_RE.match(d.stem))
    print(f"scoring {len(diffs)} diffs ...", flush=True)
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for r in pool.map(score_one, diffs):
            if r:
                rr = derived(r)
                rows.append(rr)
                gb = rr["genuine_bug"]
                print(f"  {rr['feature']:>22} {rr['engine']:>7} {rr['arm']:>2} r{rr['run']}: "
                      f"{rr['status']} all_pass={rr['all_pass']} genuine_bug={gb}", flush=True)
    (HERE / "exec_scores_v2.json").write_text(json.dumps(rows, indent=2))
    _report(rows)


def _report(rows: list[dict]) -> None:
    scorable = [r for r in rows if r["genuine_bug"] is not None]
    arms = ["B", "Bp"]
    engines = ["claude", "haiku", "codex", "kimi"]
    out = ["# v2 Results — genuine-bug rate by execution (independent blind scoring)", "",
           f"Scored runs: {len(scorable)} (of {len(rows)} diffs; non-scorable = "
           f"{len(rows) - len(scorable)} apply/exec errors).",
           "Genuine-bug = at least one **genuine** acceptance criterion fails on execution. "
           "Contract failures (arbitrary interface the model wasn't told) are excluded here.",
           "Intervals are 95% Wilson. **A green build does not count** — correctness is "
           "execution against the criteria.", ""]

    # Primary: pooled genuine-bug rate per arm
    out.append("## Genuine-bug rate, pooled across models")
    out.append("| Arm | runs | genuine-bug | rate | 95% CI |")
    out.append("|---|---|---|---|---|")
    for arm in arms:
        rs = [r for r in scorable if r["arm"] == arm]
        k = sum(r["genuine_bug"] for r in rs)
        p, lo, hi = wilson(k, len(rs))
        out.append(f"| {arm} ({'raw' if arm == 'B' else 'with spec'}) | {len(rs)} | "
                   f"{k} | **{p:.0%}** | [{lo:.0%}, {hi:.0%}] |")
    out.append("\nH2 is supported iff the B and Bp intervals do not overlap.\n")

    # Per model x arm
    out.append("## Per model — genuine-bug rate and all-pass rate")
    out.append("| Model | arm | runs | genuine-bug rate | all-5-pass rate |")
    out.append("|---|---|---|---|---|")
    for e in engines:
        for arm in arms:
            rs = [r for r in scorable if r["engine"] == e and r["arm"] == arm]
            if not rs:
                continue
            gb = sum(r["genuine_bug"] for r in rs)
            ap = sum(r["all_pass"] for r in rs)
            out.append(f"| {e} | {arm} | {len(rs)} | {gb}/{len(rs)} ({gb/len(rs):.0%}) | "
                       f"{ap}/{len(rs)} ({ap/len(rs):.0%}) |")
    out.append("")

    # Per-cell variance (the non-determinism story)
    out.append("## Per-cell variance across the 3 runs (non-determinism)")
    out.append("Cells where the 3 runs disagree on all-5-pass — a single run would have been "
               "misleading.")
    cells = defaultdict(list)
    for r in scorable:
        cells[(r["feature"], r["engine"], r["arm"])].append(r["all_pass"])
    unstable = {k: v for k, v in cells.items() if len(set(v)) > 1}
    out.append(f"\nUnstable cells: **{len(unstable)} of {len(cells)}** "
               f"({len(unstable)/max(1,len(cells)):.0%}).")
    for (fid, e, arm), vals in sorted(unstable.items()):
        out.append(f"- {fid} {e} {arm}: all-pass across runs = {['Y' if v else 'N' for v in vals]}")
    out.append("")

    text = "\n".join(out) + "\n"
    (HERE / "RESULTS.md").write_text(text)
    print("\n" + text)


if __name__ == "__main__":
    main()
