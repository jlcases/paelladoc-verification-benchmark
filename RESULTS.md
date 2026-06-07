# v2 Results — genuine-bug rate by execution (independent blind scoring)

Scored runs: 210 (of 210 diffs; non-scorable = 0 apply/exec errors).
Genuine-bug = at least one **genuine** acceptance criterion fails on execution. Contract failures (arbitrary interface the model wasn't told) are excluded here.
Intervals are 95% Wilson. **A green build does not count** — correctness is execution against the criteria.

## Genuine-bug rate, pooled across the 4 pre-registered models
| Arm | runs | genuine-bug | rate | 95% CI |
|---|---|---|---|---|
| B (raw) | 60 | 24 | **40%** | [29%, 53%] |
| Bp (with spec) | 60 | 0 | **0%** | [0%, 6%] |

H2 is supported iff the B and Bp intervals do not overlap.

## Per model — genuine-bug rate and all-pass rate
| Model | arm | runs | genuine-bug rate | all-5-pass rate |
|---|---|---|---|---|
| Claude Sonnet 4.6 | B | 15 | 5/15 (33%) | 6/15 (40%) |
| Claude Sonnet 4.6 | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| Claude Haiku 4.5 | B | 15 | 8/15 (53%) | 6/15 (40%) |
| Claude Haiku 4.5 | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| Codex (CLI default) | B | 15 | 5/15 (33%) | 8/15 (53%) |
| Codex (CLI default) | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| Kimi | B | 15 | 6/15 (40%) | 5/15 (33%) |
| Kimi | Bp | 15 | 0/15 (0%) | 15/15 (100%) |

## Frontier extension (added after the pre-registration)
Not part of the original pre-registered design. After the first 120 runs, the fair question was whether the strongest configs a skeptic would name — Opus 4.8 at high effort, Codex 5.5 at xhigh — close the raw gap on their own. Same protocol, same blind execution gate, same five features and AC tags.

| Config | arm | runs | genuine-bug rate | all-5-pass rate |
|---|---|---|---|---|
| Claude Opus 4.8 · xhigh | B | 15 | 2/15 (13%) | 8/15 (53%) |
| Claude Opus 4.8 · xhigh | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| Claude Opus 4.8 · max | B | 15 | 2/15 (13%) | 10/15 (67%) |
| Claude Opus 4.8 · max | Bp | 15 | 0/15 (0%) | 15/15 (100%) |
| Codex 5.5 · xhigh | B | 15 | 5/15 (33%) | 8/15 (53%) |
| Codex 5.5 · xhigh | Bp | 15 | 0/15 (0%) | 15/15 (100%) |

## Per-cell variance across the 3 runs (non-determinism)
Cells where the 3 runs disagree on all-5-pass — a single run would have been misleading.

Unstable cells: **11 of 70** (16%).
- f1_quake_filter codex B: all-pass across runs = ['N', 'Y', 'N']
- f1_quake_filter codex55xhigh B: all-pass across runs = ['Y', 'N', 'N']
- f1_quake_filter haiku B: all-pass across runs = ['N', 'N', 'Y']
- f1_quake_filter opusxhigh B: all-pass across runs = ['N', 'Y', 'N']
- f2_health_routes haiku B: all-pass across runs = ['N', 'Y', 'Y']
- f2_health_routes kimi B: all-pass across runs = ['Y', 'N', 'N']
- f3_spaceweather_cache codex B: all-pass across runs = ['Y', 'N', 'N']
- f3_spaceweather_cache codex55xhigh B: all-pass across runs = ['N', 'Y', 'N']
- f3_spaceweather_cache kimi B: all-pass across runs = ['N', 'Y', 'N']
- f3_spaceweather_cache opusmax B: all-pass across runs = ['N', 'Y', 'N']
- f3_spaceweather_cache opusxhigh B: all-pass across runs = ['N', 'N', 'Y']

