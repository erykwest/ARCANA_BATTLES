# P0 pre-refactor baseline — seed 1

Baseline commit: `079e944f162eaebaabfd3d833ea085d920b2d4e0`
Comparison branch commit tested: `4201353a569468d1669dda3155b8e47d20fbf354`
Points: 1000
Seed: 1

## Exact baseline vs branch comparison

All six fingerprints matched exactly: **0 mismatches / 6 series**.

| Series | Baseline winner | Branch winner | Sim time baseline / branch | Exact |
|---|---|---|---:|---:|
| 20 Hz | red | red | 177.950 / 177.950 s | YES |
| 20 Hz reverse | red | red | 309.200 / 309.200 s | YES |
| 30 Hz | red | red | 145.433 / 145.433 s | YES |
| 30 Hz reverse | blue | blue | 600.000 / 600.000 s | YES |
| 60 Hz | red | red | 184.700 / 184.700 s | YES |
| 60 Hz reverse | blue | blue | 311.633 / 311.633 s | YES |

## What this proves

1. The refactor branch tooling did not change simulation output for this controlled seed: every recorded fingerprint field is identical to baseline.
2. The current engine is materially timestep-sensitive: the same seed produces substantially different battle duration and combat state at 20/30/60 Hz.
3. The current engine is materially iteration-order-sensitive: reversing `State.units` changes the winner at 30 Hz and 60 Hz for this seed.
4. This is a smoke/baseline fixture, not a statistical balance sample. It exists to preserve a concrete pre-refactor reference before fixed timestep/RNG/Intel changes.

## Canonical fingerprint highlights

### 20 Hz normal
- Winner: red
- End: 177.950 s
- Blue lost: 1000 PT
- Red lost: 0 PT

### 30 Hz normal
- Winner: red
- End: 145.433 s
- Blue lost: 1000 PT
- Red lost: 0 PT

### 60 Hz normal
- Winner: red
- End: 184.700 s
- Blue lost: 1000 PT
- Red lost: 80 PT

### 20 Hz reverse
- Winner: red
- End: 309.200 s
- Blue lost: 1000 PT
- Red lost: 415 PT

### 30 Hz reverse
- Winner: blue at time limit
- End: 600.000 s
- Blue lost: 480 PT
- Red lost: 885 PT

### 60 Hz reverse
- Winner: blue
- End: 311.633 s
- Blue lost: 290 PT
- Red lost: 995 PT
