# P0 fixed-step determinism — after refactor

Canonical physics tick: **1/30 s (30 Hz)**
Branch: `refactor/p0-determinism`
Historical baseline: `079e944f162eaebaabfd3d833ea085d920b2d4e0`

## Seed 1 before → after

Before the fixed-step refactor, seed 1 changed duration, final state and even winner when the diagnostic driver cadence or `State.units` iteration order changed.

| Scenario | Before | After |
|---|---:|---:|
| 20 Hz | RED @ 177.950 s | RED @ 145.433 s |
| 20 Hz reverse | RED @ 309.200 s | RED @ 145.433 s |
| 30 Hz | RED @ 145.433 s | RED @ 145.433 s |
| 30 Hz reverse | BLUE @ 600.000 s | RED @ 145.433 s |
| 60 Hz | RED @ 184.700 s | RED @ 145.433 s |
| 60 Hz reverse | BLUE @ 311.633 s | RED @ 145.433 s |

The post-refactor gate compares the meaningful final fingerprint, not only the winner. For seed 1 all six scenarios are exact matches.

## What changed

- browser simulation uses an accumulator and `CFG.SIM_FIXED_DT = 1/30`;
- rendering cadence is decoupled from physics cadence;
- every physics tick canonicalizes `State.units` by stable unit id;
- Sim Lab `dt` is a driver cadence diagnostic only; physics always uses the canonical tick;
- Sim Lab AI refresh happens on fixed-step boundaries;
- Sim Lab max-time termination is based on canonical simulation time, so the final tick (including 600 s) is cadence-independent.

## Boundary regression found during validation

Seed 10 initially exposed a headless-only boundary defect: 20/30 Hz stopped at 599.967 s while 60 Hz executed the canonical 600.000 s tick. The loop was corrected to stop on canonical simulation time. Seed 10 then passed all six scenarios exactly.

## Multi-seed validation

Validation matrix: seeds 1–10 × {20,30,60 Hz} × {normal, reverse}.

At the latest recorded checkpoint, **8/10 seeds have completed with zero fingerprint mismatches (48/48 exact comparisons)**. The remaining long-running seeds are retained as regression cases because they exercise battles close to the 600 s limit.

This file records determinism only. It does not claim that the new canonical-tick results preserve aggregate balance versus the pre-refactor variable-timestep population; that requires a separate statistical baseline/branch balance run after P0 determinism is locked.
