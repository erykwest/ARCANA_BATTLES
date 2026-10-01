# P0.4 — Intel LOS cache validation

Branch: `refactor/p0-determinism`

Engine cache commit: `2fec264c7a49c12a9ff76e4769a8216bf2c39043`

## Change

The three semantic `Intel.update()` phases remain in the fixed-step pipeline:

1. pre AI / orders;
2. post movement / contacts, pre ranged;
3. post combat.

No visibility phase was deleted or moved.

The optimization is below that semantic layer: `Intel.canSeeNow()` now reuses a pair-level visibility result for `viewer -> enemy` while both `Geometry.center()` values are unchanged. The cache is reset with Intel state at battle reset.

This avoids repeated distance / terrain LOS work from `Intel.update()`, AI, ranged targeting and rendering without changing what each phase is allowed to know.

## Seed 1 benchmark

Canonical 30 Hz battle:

- winner: RED;
- simulation end: 145.433 s;
- pair visibility checks: 898,713;
- cache hits: 784,337;
- cache misses: 114,376;
- terrain LOS checks after cache: 22,703;
- cache entries at end: 112;
- pair-cache hit rate: 87.27%.

The hit rate is not claimed as an equal wall-clock speedup; it measures reused pair-visibility evaluations.

## Semantic regression

### Seed 1 — full six-scenario pre/post comparison

The complete recorded fingerprints before and after the Intel cache are identical field-by-field for:

- 20 Hz driver;
- 20 Hz driver + reverse unit array;
- 30 Hz driver;
- 30 Hz driver + reverse unit array;
- 60 Hz driver;
- 60 Hz driver + reverse unit array.

Result: **0 pre/post fingerprint differences**.

### Seed 2 — canonical long case

- pre-cache: RED @ 268.567 s;
- post-cache: RED @ 268.567 s;
- canonical fingerprint: identical field-by-field;
- canonical JS-stable SHA-256: `09c9c11b55e3d76f5a2943bcdab2d5576ec41308ca70c73a0bdc784d23e94c73`.

### Seed 5 — time-limit long case

- pre-cache: BLUE @ 600 s;
- post-cache: BLUE @ 600 s;
- canonical JS-stable SHA-256 before/after: `1777188bcd75fdf0ebbe364a4553fa1820052213c03b9f7d101c255aaaa9f677`.

The general six-scenario CI job for seed 5 still exceeds its 10-minute runner timeout; this is a test-runtime limitation, not a determinism failure. A dedicated canonical fingerprint verifier covers the long case.

## Outcome

**P0.4 PASS.**

The Intel pipeline keeps its existing semantics while avoiding the majority of repeated pair-level visibility evaluation on the benchmark battle.

Next P0 item: replace gameplay `Math.random()` use and Sim Lab's global `Math.random` monkey-patch with an explicit seeded engine RNG.
