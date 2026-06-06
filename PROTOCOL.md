# Does an explicit spec + a verification gate make AI-generated code correct? — Protocol (v2)

Pre-registered methodology. Written before the v2 runs so the analysis can't be fit to the
result. v1 was a directional probe (n=5, one run per cell); this version fixes its four real
weaknesses: single-run noise under non-determinism, the "told → passes" near-tautology,
subjective failure classification, and an in-house arm that read as a vendor benchmark.

This benchmark is **tool-agnostic**. It does not put any product in the arms. It measures one
thing: whether giving a coding agent explicit acceptance criteria up front, and scoring "done"
by executing the code, changes how often the result is actually correct — across several models.

Status: **pre-registration**. Numbers are filled into `RESULTS.md` only after the runs complete,
following the analysis plan below verbatim.

---

## 1. Research questions

- **RQ1.** When an AI coding agent finishes a task and the project builds green, how often is
  the code actually correct, verified by executing it against acceptance criteria?
- **RQ2.** Does giving the agent the acceptance criteria up front change the correctness rate?
- **RQ3.** How does that effect vary with model cost?

## 2. Hypotheses (pre-registered)

- **H1.** A raw one-line request ships a *genuine* correctness bug in a meaningful fraction of
  runs even when the build passes.
- **H2.** Handing the agent the acceptance criteria up front reduces the genuine-bug rate,
  distinguishably (non-overlapping 95% intervals between arm B and arm Bp on the pooled rate).
- **H3.** The absolute reduction is larger for cheaper models than for the frontier model.

We commit to reporting H1–H3 whether they hold or not, including where they fail. A null or
reversed result is reported as found.

## 3. Frozen setup

- **Repo.** One real Next.js + TypeScript application (codename "Osiris"), pinned at commit
  `37c4cc4`; baseline builds green with 0 type errors. The commit hash is recorded in `RESULTS.md`.
- **Features.** 5 invented features, each a one-line request, a user story, and exactly 5
  acceptance criteria. Frozen in `features.json` before any run. (More features / a second repo
  are explicitly out of scope for v2 and named as future work — see §9.)
- **Isolation.** Every run executes in its own detached git worktree branched from `37c4cc4`.
  No run can see or contaminate another.
- **Models (4).** Claude Sonnet 4.6 (frontier), Claude Haiku 4.5 (cheap), Codex, Kimi —
  spanning frontier to ~10–50× cheaper. Sonnet and Haiku run on the same CLI with only the model
  flag changed, giving a clean cheap-vs-frontier contrast within one family. Run-time versions
  are recorded in `RESULTS.md`.

## 4. The two arms (no product is an arm)

Each arm is the *input the agent gets*; model and flags are held constant within a cell.

- **B — raw.** The one-line request only. What a user actually types.
- **Bp — raw + acceptance criteria.** The same request plus the 5 acceptance criteria as a
  plaintext checklist.

We deliberately do **not** include an arm for any specific tool. v1 had a "PaellaDoc" arm; we
dropped it on purpose. Putting our own product in the ring would make this a vendor benchmark and
invite "you rigged it." The honest, defensible claim is about the *principle* — does an explicit
spec change correctness — measured tool-agnostically. Any tool that generates the spec and runs
the gate (PaellaDoc is one) operationalizes the principle; that belongs in the discussion, not
in the experiment.

## 5. Scoring — independent and blind (separates measurement from anything it could favor)

All diffs from both arms are scored by a single, independent **execution gate**: re-apply the
diff to a fresh frozen worktree, import the route handler, call it with real Requests (upstream
fetch mocked deterministically inside the test), and assert each acceptance criterion *in code*
(`ac_tests/*.ts`, one per feature). The scorer is given no arm label and applies the
identical assertions to every arm.

**A green build does not count.** `tsc --noEmit` + `next build` passing is recorded separately and
is not the correctness signal. Correctness = the acceptance criteria execute as specified.

## 6. Genuine vs contract — pre-classified, not judged post-hoc

Each acceptance criterion is tagged `genuine` or `contract` in `features.json`, **before any run**:

- `genuine` — any competent implementation should satisfy it without being told the exact
  interface (no crash on bad input, correct base case, internal consistency, preserve existing
  behavior).
- `contract` — an arbitrary interface choice the model cannot know unless told (a parameter
  spelled `minMag` vs `minMagnitude`, an ordering policy, case-handling).

The **primary metric counts only `genuine` failures.** Contract failures are reported separately
and excluded from the headline, on purpose: the raw arm can't be faulted for an interface it was
never given. The split is a mechanical computation over the pre-committed tagging — anyone can
reproduce it from the raw data, no per-failure discretion. (Worked example: a raw run that
implements the filter under `minMag` fails the `minMagnitude` criterion — a *contract* miss,
not counted as a genuine bug.)

## 7. Design and runs

- Cells = feature (5) × model (4) × arm (2) = 40 cells.
- **k = 3 runs per cell → 120 runs**, each in its own worktree.
- Multiple runs per cell is the fix for LLM non-determinism: floating-point non-associativity and
  provider-side batching mean even temperature 0 is not reproducible across calls. One run per
  cell measures a single draw; three measure the spread.

## 8. Analysis plan (pre-registered)

Run only after all 120 runs are scored.

- **Primary.** *Genuine-bug rate* per arm = fraction of runs with ≥1 failed `genuine` AC, with a
  95% **Wilson** confidence interval. H2 is supported iff the B and Bp intervals do not overlap.
- **Per-cell variance.** For each cell, the spread of the 3 runs (all-pass agreement). Reported as
  its own finding — how misleading a single run would have been. The non-determinism story,
  quantified.
- **Secondary.** All-5-ACs-pass rate; build-green rate (to show green ≠ correct); per-AC pass
  rate; cost-to-correctness ($/task from documented public per-token prices + measured Claude
  totals, method in `RESULTS.md`).
- **Per-model breakdown** for H3.
- No metric is added or swapped after seeing results. Anything noticed post-hoc is labeled
  exploratory.

## 9. Threats to validity (stated, not hidden)

- **Coverage.** 5 features, one repo, one stack. Directional for "real AI coding," not a universal
  law. More features and a second repo/stack are named future work.
- **Told → passes.** Arm Bp is given the criteria the gate then checks. Mitigated by (a) the
  independent blind scorer applying the *same* assertions to both arms, and (b) the
  genuine/contract split. The comparison is honest: it measures the value of telling the agent the
  criteria, not a tautology, because the raw arm is held to the identical assertions.
- **Model drift.** Hosted models change under fixed names; run-time versions are recorded.
  Results are a snapshot, not a permanent ranking.
- **Raw-arm minimality.** The one-liner is deliberately minimal — it is the realistic baseline
  (what people type), not a strawman; Bp is the same request plus the checklist.
- **Non-determinism.** Addressed by k=3, not eliminated; the variance section reports residual
  instability.

## 10. Reproducibility

- **The harness and scoring are fully reproducible:** frozen repo commit, the executable AC tests,
  the gate, the features and their AC tags are all published. Anyone can re-score the published
  diffs and reproduce every number.
- **The agent outputs are not bit-reproducible** by design (non-determinism). A re-run produces
  different diffs; "reproducible" here means the *protocol and the scoring*, plus the published
  artifacts (every diff, every per-run verdict). Stated plainly so no one mistakes it for
  determinism.
- **Published:** this protocol, `features.json` (with AC tags), the runner (`run_v2.py`), the
  scorer (`score_v2.py`), the AC tests (`ac_tests/`), `runs/` (all 120 diffs +
  per-run metadata + scores), and `RESULTS.md` (numbers + run-time model versions + commit hash).
  Nothing relevant to reproduction is withheld.

---

*Protocol frozen on the date in this file's git history. Results follow in `RESULTS.md` once the
runs complete and are scored.*
