# Simulation tools

## Permanent regression suite

The permanent CI entry point is `.github/workflows/simulation-regression.yml`.

### Automatic smoke

Runs on changes to the simulation runtime (`COFFEE_BATTLES.html`, `sim-lab.js`) on `main` and `refactor/p0-determinism`.

It executes seed 1 across:

- 20 Hz driver;
- 30 Hz driver;
- 60 Hz driver;
- the same three cases with reversed unit-array order.

All six fingerprints must be identical to the canonical 30 Hz result.

### Manual full suite

Run **Simulation regression → Run workflow → full**.

It runs the smoke matrix plus canonical SHA-256 checks for seeds 1, 2 and 5. These cover a normal battle, a long battle and the 600 s battle-limit case.

Canonical hashes are intentionally stored in the workflow. A gameplay change that legitimately alters them must be reviewed explicitly before updating the expected values.

## Baseline / balance analysis

`baseline-matrix.js` remains the heavier exploratory tool for 20/30/60 Hz, reverse-order and multi-seed batches. It is not automatic CI because 50–500 seed runs are expensive.

## Performance benchmark

`run-intel-cache-benchmark.mjs` is retained for explicit Intel/LOS performance measurements. Performance metrics are not regression fingerprints.

## Rule

Simulation changes should pass automatic smoke before merge. Run the full suite before milestones, major engine changes or deliberate rebalance work.
