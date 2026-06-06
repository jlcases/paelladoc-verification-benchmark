# v2 Results — genuine-bug rate by execution (independent blind scoring)

Scored runs: 120 (of 120 diffs; non-scorable = 0 apply/exec errors).
Genuine-bug = at least one **genuine** acceptance criterion fails on execution. Contract failures (arbitrary interface the model wasn't told) are excluded here.
Intervals are 95% Wilson. **A green build does not count** — correctness is execution against the criteria.

## Genuine-bug rate, pooled across models
| Arm | runs | genuine-bug | rate | 95% CI |
|---|---|---|---|---|
| B (raw) | 60 | 24 | **40%** | [29%, 53%] |
| Bp (with spec) | 60 | 0 | **0%** | [0%, 6%] |

H2 is supported iff the B and Bp intervals do not overlap.

## Per model — genuine-bug rate and all-pass rate
| Model | arm | runs | genuine-bug rate | all-5-pass rate |
|---|---|---|---|---|
| claude | B | 15 | 5/15 (33%) | 6/15 (40%) |
| claude | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| haiku | B | 15 | 8/15 (53%) | 6/15 (40%) |
| haiku | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| codex | B | 15 | 5/15 (33%) | 8/15 (53%) |
| codex | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| kimi | B | 15 | 6/15 (40%) | 5/15 (33%) |
| kimi | Bp | 15 | 0/15 (0%) | 15/15 (100%) |

## Per-cell variance across the 3 runs (non-determinism)
Cells where the 3 runs disagree on all-5-pass — a single run would have been misleading.

Unstable cells: **6 of 40** (15%).
- f1_quake_filter codex B: all-pass across runs = ['N', 'Y', 'N']
- f1_quake_filter haiku B: all-pass across runs = ['N', 'N', 'Y']
- f2_health_routes haiku B: all-pass across runs = ['N', 'Y', 'Y']
- f2_health_routes kimi B: all-pass across runs = ['Y', 'N', 'N']
- f3_spaceweather_cache codex B: all-pass across runs = ['Y', 'N', 'N']
- f3_spaceweather_cache kimi B: all-pass across runs = ['N', 'Y', 'N']

