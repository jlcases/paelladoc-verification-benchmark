#!/usr/bin/env python3
"""v2 runner (tool-agnostic). For each cell (feature x engine x arm) run k times, each in an
isolated git worktree off the frozen commit, same model & flags. Two arms:
  B  (raw)     : the one-line request only.
  Bp (raw+ACs) : the request + the same acceptance criteria as a plaintext checklist.
No PaellaDoc arm: this measures whether giving the agent the acceptance criteria up front
improves correctness, across models. Scoring is done separately and blind by score_v2.py.

Each run writes runs/<fid>__<engine>__<arm>__r<run>.diff and a sibling .json with build-green
+ cost + status. Resumable: a cell-run with an existing .diff is skipped.

Usage:
  BENCH_REPO=/path/to/osiris python3 run_v2.py            # full matrix (k=3)
  python3 run_v2.py --smoke                               # 1 feature, all engines, both arms, 1 run
  python3 run_v2.py --features f1_quake_filter --engines claude --runs 1
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
_BENCH = os.environ.get("BENCH_REPO")
if not _BENCH:
    raise SystemExit("set BENCH_REPO=/path/to/osiris (the frozen Next.js test repo, at 37c4cc4)")
OSIRIS = Path(_BENCH)
NODE_MODULES = OSIRIS / "node_modules"
FROZEN = "37c4cc4"
WORKROOT = Path("/tmp/bench_v2")
RUNS = HERE / "runs"
FEATURES = json.load(open(HERE / "features.json"))
ARMS = ("B", "Bp")
# Core (pre-registered): the original 4 models. Frontier extension (added after the first 120,
# labeled as such in RESULTS — NOT part of the pre-registration): the strongest configs a
# skeptic would name — Opus 4.8 at xhigh and max effort, Codex 5.5 at xhigh.
CORE_ENGINES = ("claude", "haiku", "codex", "kimi")
EXT_ENGINES = ("opusxhigh", "opusmax", "codex55xhigh")
ENGINES = CORE_ENGINES + EXT_ENGINES

# claude/haiku/opus run on the same `claude` CLI, only model (+effort) change. codex uses its
# CLI default model; codex55xhigh pins gpt-5.5 at xhigh reasoning. kimi uses its default.
MODEL = {"claude": "claude-sonnet-4-6", "haiku": "claude-haiku-4-5",
         "opusxhigh": "claude-opus-4-8", "opusmax": "claude-opus-4-8"}
EFFORT = {"opusxhigh": "xhigh", "opusmax": "max"}


def build_prompt(feat: dict, arm: str) -> str:
    acs = "\n".join(f"  {i + 1}. {a}" for i, a in enumerate(feat["acs"]))
    tail = ("\nEdit files directly. When finished, make sure the project still type-checks "
            "(`npx tsc --noEmit`) and builds (`npm run build`).")
    if arm == "B":
        return (f"You are working in this Next.js + TypeScript repository.\n\n"
                f"Implement this change:\n\n{feat['request']}{tail}")
    return (f"You are working in this Next.js + TypeScript repository.\n\n"
            f"Implement this change:\n\n{feat['request']}\n\n"
            f"It must satisfy ALL of these acceptance criteria:\n{acs}{tail}")


def run_engine(engine: str, prompt: str, cwd: Path) -> dict:
    if engine in ("claude", "haiku", "opusxhigh", "opusmax"):
        cmd = ["claude", "--print", prompt, "--model", MODEL[engine],
               "--output-format", "stream-json", "--verbose",
               "--permission-mode", "bypassPermissions", "--dangerously-skip-permissions"]
        if engine in EFFORT:
            cmd += ["--effort", EFFORT[engine]]
        timeout = 2400 if engine in EFFORT else 1200
    elif engine in ("codex", "codex55xhigh"):
        cmd = ["codex", "exec", prompt, "--dangerously-bypass-approvals-and-sandbox",
               "--skip-git-repo-check"]
        if engine == "codex55xhigh":
            cmd += ["-m", "gpt-5.5", "-c", "model_reasoning_effort=xhigh"]
        timeout = 2400 if engine == "codex55xhigh" else 1200
    elif engine == "kimi":
        cmd = ["kimi", "-p", prompt, "--yolo", "--print", "-w", str(cwd)]
        timeout = 1800
    else:
        raise ValueError(engine)
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True, "cost_usd": None}
    cost = None
    if engine in ("claude", "haiku", "opusxhigh", "opusmax"):
        for ln in proc.stdout.splitlines():
            try:
                ev = json.loads(ln)
            except ValueError:
                continue
            if ev.get("type") == "result":
                cost = ev.get("total_cost_usd")
    return {"ok": proc.returncode == 0, "timeout": False, "cost_usd": cost}


def setup_worktree(wt: Path) -> None:
    if wt.exists():
        subprocess.run(["git", "-C", str(OSIRIS), "worktree", "remove", "--force", str(wt)],
                       capture_output=True)
        shutil.rmtree(wt, ignore_errors=True)
    subprocess.run(["git", "-C", str(OSIRIS), "worktree", "add", "--detach", str(wt), FROZEN],
                   capture_output=True, check=True)
    subprocess.run(["cp", "-cR", str(NODE_MODULES), str(wt / "node_modules")], check=True)


def teardown_worktree(wt: Path) -> None:
    shutil.rmtree(wt / "node_modules", ignore_errors=True)
    shutil.rmtree(wt / ".next", ignore_errors=True)
    subprocess.run(["git", "-C", str(OSIRIS), "worktree", "remove", "--force", str(wt)],
                   capture_output=True)


def gate_build_green(wt: Path) -> bool:
    tsc = subprocess.run(["npx", "tsc", "--noEmit"], cwd=str(wt), capture_output=True, text=True)
    if tsc.returncode != 0:
        return False
    build = subprocess.run(["npm", "run", "build"], cwd=str(wt), capture_output=True, text=True)
    return build.returncode == 0


def do_run(feat: dict, engine: str, arm: str, run_idx: int) -> None:
    stem = f"{feat['id']}__{engine}__{arm}__r{run_idx}"
    diff_path = RUNS / f"{stem}.diff"
    if diff_path.exists():
        print(f"  skip (exists) {stem}", flush=True)
        return
    wt = WORKROOT / stem
    setup_worktree(wt)
    prompt = build_prompt(feat, arm)
    print(f"  run {stem} ...", flush=True)
    agent = run_engine(engine, prompt, wt)
    # Stage everything (respecting .gitignore → node_modules/.next excluded) so NEW files the
    # agent created are captured. Plain `git diff` misses untracked files, which silently
    # produced incomplete diffs (route imports a new module that wasn't in the patch).
    subprocess.run(["git", "-C", str(wt), "add", "-A"], capture_output=True)
    diff = subprocess.run(["git", "-C", str(wt), "diff", "--cached"],
                          capture_output=True, text=True).stdout
    build_green = gate_build_green(wt) if diff.strip() else False
    diff_path.write_text(diff)
    (RUNS / f"{stem}.json").write_text(json.dumps({
        "feature": feat["id"], "engine": engine, "arm": arm, "run": run_idx,
        "empty_diff": not diff.strip(), "build_green": build_green,
        "agent_ok": agent["ok"], "timeout": agent["timeout"], "cost_usd": agent["cost_usd"],
    }, indent=2))
    print(f"    {stem}: diff={'empty' if not diff.strip() else 'ok'} "
          f"build_green={build_green} cost={agent['cost_usd']}", flush=True)
    teardown_worktree(wt)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", nargs="*", default=[f["id"] for f in FEATURES])
    ap.add_argument("--engines", nargs="*", default=list(ENGINES))
    ap.add_argument("--arms", nargs="*", default=list(ARMS))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--smoke", action="store_true",
                    help="1 feature, all engines, both arms, 1 run")
    a = ap.parse_args()
    if a.smoke:
        a.features = [FEATURES[0]["id"]]
        a.runs = 1
    RUNS.mkdir(exist_ok=True)
    WORKROOT.mkdir(parents=True, exist_ok=True)
    feats = [f for f in FEATURES if f["id"] in a.features]
    total = len(feats) * len(a.engines) * len(a.arms) * a.runs
    print(f"matrix: {len(feats)} features x {len(a.engines)} engines x {len(a.arms)} arms "
          f"x {a.runs} runs = {total} runs", flush=True)
    n = 0
    for f in feats:
        for engine in a.engines:
            for arm in a.arms:
                for r in range(1, a.runs + 1):
                    n += 1
                    print(f"[{n}/{total}]", end=" ")
                    do_run(f, engine, arm, r)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
