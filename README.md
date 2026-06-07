# A green build is not a correct feature — a reproducible benchmark

Does giving an AI coding agent the **acceptance criteria up front**, and scoring "done" by
**executing the code** against them, change how often the result is actually correct? Measured
across 4 models, every cell run 3 times.

This is **tool-agnostic**. No product is in the arms. It tests a principle, not a vendor.

- **Method (read this first):** [`PROTOCOL.md`](./PROTOCOL.md) — pre-registered before the runs.
- **Results:** [`RESULTS.md`](./RESULTS.md) — 120 pre-registered runs (raw 40% genuine bugs, spec 0%) plus a labeled frontier extension (Opus 4.8 at xhigh/max, Codex 5.5 at xhigh): even Opus 4.8 at max effort ships a genuine bug in 13% of raw runs, 2 of 3 on the hard feature, non-deterministically; the spec takes every config to 0%.
- **Every run:** [`runs/`](./runs/) — all diffs + per-run verdicts.

## The one-paragraph version

When an agent finishes a coding task and the project builds green, the work *looks* done.
"Builds green" and "does what was asked" are different claims, and the gap is wider than it
feels. This benchmark measures the gap by **running** the code and asserting each acceptance
criterion — a green build doesn't count — and tests whether handing the agent the criteria up
front closes it.

## Design (one screen)

- **Repo:** a real Next.js + TypeScript app, frozen at one commit (`37c4cc4`), builds green at
  baseline. 5 features, each a user story + 5 acceptance criteria, frozen in `features.json`.
- **Two arms:** `B` = the raw one-line request (what people type); `Bp` = the same request plus
  the 5 acceptance criteria as a checklist. No tool-specific arm, on purpose.
- **4 models:** Claude Sonnet 4.6 (frontier), Claude Haiku 4.5 (cheap), Codex, Kimi.
- **k = 3 runs per cell** (40 cells → 120 runs), each in its own isolated git worktree. Three
  runs because LLMs are non-deterministic even at temperature 0 (float non-associativity +
  provider batching); one run per cell would be a single noisy draw.
- **Scoring is independent and blind:** a separate execution gate re-applies each diff, imports
  the route, calls it with real requests, and asserts every criterion in code — the same
  assertions for both arms, no arm label.
- **Genuine vs contract:** each criterion is pre-tagged. The headline counts only **genuine**
  correctness bugs (crash, wrong base case, broken consistency); arbitrary interface mismatches
  the raw agent couldn't know (a param name) are reported separately and excluded.

## Reproduce it

```bash
# 1. point at the frozen test repo (Next.js, at commit 37c4cc4), node_modules installed
export BENCH_REPO=/path/to/osiris

# 2. run the matrix (or a subset; resumable — existing diffs are skipped)
python3 run_v2.py                          # full: 5 feat × 4 models × 2 arms × 3 runs
python3 run_v2.py --smoke                   # 1 feature, all models, both arms, 1 run

# 3. score every diff by execution (blind) → RESULTS.md
python3 score_v2.py
```

The agent runs are **not** bit-reproducible (non-determinism is the point): a re-run produces
different diffs. What's reproducible is the protocol, the gate, and the scoring — and every diff
and verdict we got is published in `runs/`, so anyone can re-score them and reproduce every
number without re-running a single agent.

## Honest limits

5 features, one repo, one stack — directional, not a paper. The `Bp` arm is given the criteria
the gate then checks; that's mitigated by scoring **both** arms with the identical independent
assertions and by the genuine/contract split, so it measures the value of telling the agent the
criteria, not a tautology. Hosted model versions drift; run-time versions are in `RESULTS.md`.
Full threat list in [`PROTOCOL.md`](./PROTOCOL.md) §9.

## Where a tool fits

If an explicit spec + an execution gate measurably helps, the practical question is who writes
the spec and runs the gate every task. Doing it by hand (the `Bp` arm) works but nobody does it
per task; a tool that generates the criteria and gates on execution automates it. That's the
operationalization — it lives in the discussion, deliberately not in the experiment.

---

*Tell me where you think the method breaks — that's the point of publishing it.*
