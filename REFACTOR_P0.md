# COFFEE BATTLES — P0 Deterministic Refactor

Branch: `refactor/p0-determinism`

## Goal

Rendere il motore **misurabile, deterministico e confrontabile** prima di qualsiasi refactor architetturale ampio.

Questo branch NON introduce build system, Vite, esbuild o modularizzazione del monolite. `COFFEE_BATTLES.html` resta l'artefatto standalone canonico.

## Regole del refactor

1. Nessun cambiamento volontario di bilanciamento durante P0.
2. Prima si misura, poi si cambia il loop.
3. Ogni modifica al runtime deve essere confrontabile con una baseline congelata.
4. Stessi seed + stesso setup + stesso tick devono produrre lo stesso risultato.
5. Browser e Sim Lab devono usare lo stesso timestep canonico per costruzione.
6. Le velocità x1/x2/x3 devono cambiare quanti tick vengono eseguiti, non la dimensione del tick.
7. Le ottimizzazioni di Intel vengono fatte solo dopo aver verificato le dipendenze intra-tick di AI, movimento, ranged e combat.
8. Nessun refactor generale di Terrain/AI/UI entra in P0 salvo ciò che serve a determinismo e robustezza.

## Stato P0

- P0.0 — baseline timestep sensitivity: **DONE**
- P0.1 — safe storage: **DONE**
- P0.2 — fixed timestep browser: **DONE**
- P0.3 — Sim Lab allineato al tick canonico: **DONE**
- P0.4 — Intel/LOS cache senza semantic drift: **DONE**
- P0.5 — RNG gameplay esplicito e seedabile: **DONE**
- P0.6 — regression suite permanente: **DONE**

## Baseline e tick canonico

Il motore storico mostrava sensibilità significativa sia al timestep sia all'ordine dell'array unità. Il tick canonico scelto è 30 Hz.

Il browser usa un accumulatore fixed-step; x1/x2/x3 cambiano il numero di tick simulati per secondo reale, non il dt del singolo tick. Sim Lab usa lo stesso tick canonico, mantenendo override diagnostici 20/30/60 Hz per i gate di determinismo.

## Intel pipeline

Le tre fasi semantiche Intel restano nel pipeline:

1. pre AI / orders;
2. post movement / contacts, pre ranged;
3. post combat.

L'ottimizzazione P0.4 è sotto quel livello: cache pair-level delle verifiche di visibilità/LOS, invalidata dal cambiamento delle geometrie osservatore/bersaglio. Il benchmark seed 1 ha mostrato circa 87% di cache hit senza variazione dei fingerprint canonici.

## RNG

La casualità gameplay passa da `Random.next()`. Il Sim Lab usa `Random.setSeed(seed)` e ripristina poi la sorgente precedente; non monkey-patcha più `Math.random` globale.

## Regression suite permanente

Workflow canonico: `.github/workflows/simulation-regression.yml`.

### Smoke automatico

Su modifiche a `COFFEE_BATTLES.html`, `sim-lab.js` o ai runner di regression, su `main` e `refactor/p0-determinism`:

- seed 1;
- 20 / 30 / 60 Hz;
- normal / reverse unit-array order;
- tutti i fingerprint devono essere identici al 30 Hz canonico.

### Full manuale

`workflow_dispatch` con `suite=full` esegue lo smoke più i fingerprint SHA-256 canonici dei seed 1, 2 e 5.

Gli hash canonici non vanno aggiornati automaticamente: un cambiamento legittimo di gameplay deve essere reviewato esplicitamente.

## Tooling mantenuto

- `tools/baseline-matrix.js` — analisi multi-seed pesante / balance exploration;
- `tools/run-p0-determinism-gate.mjs` — invariance 20/30/60 + reverse;
- `tools/run-p0-canonical-fingerprint.mjs` — verifica exact canonical state;
- `tools/run-intel-cache-benchmark.mjs` — profiling Intel/LOS.

I vecchi workflow one-shot `apply-*` e i runner temporanei del refactor sono stati rimossi.

## Dopo P0

### P1 — consolidamento interno

- rimuovere lo state swap temporaneo di `State.terrain` in `Terrain.draw`;
- assorbire progressivamente i wrapper `legacy*` nelle implementazioni canoniche;
- mantenere la regression suite come gate per ogni intervento sul simulation core.

### P2 — scaling

- selected panel dirty/throttled;
- i18n generato direttamente da key;
- ulteriori ottimizzazioni solo se misurate.

### P3 — pubblicazione

- CMP AdSense / verifica UE;
- security headers Vercel;
- README e metadata sito.
