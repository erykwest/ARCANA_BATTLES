# COFFEE BATTLES

Standalone browser tactical battle lab.

Current development principle: keep `COFFEE_BATTLES.html` as the canonical standalone artifact. GitHub/Vercel are used for versioning and deployment, not as a reason to introduce a build system prematurely.

Simulation-core changes are protected by `.github/workflows/simulation-regression.yml`:

- automatic smoke on runtime changes;
- manual full canonical regression before milestones or major engine work.

See `REFACTOR_P0.md` and `results/` for the deterministic-engine baseline and validation history.
