# P0.6 — Permanent simulation regression suite

Branch: `refactor/p0-determinism`

## Goal

Replace the temporary P0 GitHub Actions/workflow sprawl with one permanent regression entry point.

## Permanent CI

Workflow: `.github/workflows/simulation-regression.yml`

### Automatic smoke

Triggered by simulation-runtime changes on `main` and `refactor/p0-determinism`.

Runs seed 1 in six scenarios:

- 20 Hz;
- 20 Hz + reversed unit array;
- 30 Hz;
- 30 Hz + reversed unit array;
- 60 Hz;
- 60 Hz + reversed unit array.

Every meaningful final-state fingerprint must match the canonical 30 Hz run exactly.

### Manual full suite

Triggered with `workflow_dispatch` and `suite=full`.

Runs the smoke matrix plus canonical SHA-256 verification for:

- seed 1 — normal case;
- seed 2 — long case;
- seed 5 — battle-limit case.

Expected hashes are the fingerprints validated at the end of P0.5.

## Cleanup

Removed temporary mutation workflows (`apply-*`) and exploratory P0 workflows that were only needed while developing the refactor. Removed their one-shot patch scripts and obsolete comparison runners.

Retained reusable tooling:

- `baseline-matrix.js` for expensive exploratory/balance batches;
- `run-p0-determinism-gate.mjs` for cadence/order invariance;
- `run-p0-canonical-fingerprint.mjs` for exact canonical state verification;
- `run-intel-cache-benchmark.mjs` for explicit Intel/LOS profiling.

## Policy

- automatic CI stays lightweight;
- expensive multi-seed balance runs remain manual;
- canonical hash changes require an intentional review/update rather than silently accepting drift;
- no one-shot GitHub Actions patch workflows should be added for normal development.

## Outcome

**P0.6 complete once the new automatic smoke workflow passes on the consolidation commit.**
