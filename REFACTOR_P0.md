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
7. Le ottimizzazioni di `Intel.update()` vengono fatte solo dopo aver verificato le dipendenze intra-tick di AI, movimento, ranged e combat.
8. Nessun refactor generale di Terrain/AI/UI entra in P0 salvo ciò che serve a determinismo e robustezza.

---

## P0.0 — Baseline prima del cambio fisico

Eseguire gli stessi seed con:

- `dt = 0.05` — 20 Hz, default storico del Sim Lab;
- `dt = 1/30` — 30 Hz;
- `dt = 1/60` — 60 Hz.

Per ogni frequenza eseguire anche il bias check con `reverseUnits:true`.

Metriche minime da conservare:

- vittorie BLU / ROSSO / draw / unresolved;
- ruolo ATT / DEF;
- durata media e mediana;
- timeout / truncated / stuck;
- army collapse;
- uso unità;
- dottrine;
- differenze seed-per-seed tra ordine normale e reverse-order.

Helper: `tools/baseline-matrix.js`.

### Scelta del tick canonico

Non viene fissata a priori.

- Se 30 Hz e 60 Hz risultano sostanzialmente equivalenti, preferire 30 Hz per dimezzare il costo dei batch.
- Se emergono differenze rilevanti o tunneling/contatti instabili, usare 60 Hz.

Il confronto deve essere fatto sul comportamento, non solo sulla percentuale aggregata di vittorie.

---

## P0.1 — Robustezza storage

Proteggere `localStorage.getItem/setItem` con un piccolo adapter safe:

- fallimento lettura => fallback in memoria/default;
- fallimento scrittura => nessun crash;
- nessuna modifica al comportamento quando storage è disponibile.

È una correzione indipendente dal gameplay e va mantenuta separata dal commit del timestep.

---

## P0.2 — Fixed timestep browser

Sostituire il runtime variabile:

`realDt × timeScale -> Simulation.update(dt variabile)`

con accumulatore:

- `FIXED_DT` unico;
- `requestAnimationFrame` gestisce solo tempo reale + rendering;
- x1/x2/x3 accumulano tempo simulato;
- `Simulation.update(FIXED_DT)` viene chiamato N volte;
- cap di sicurezza per evitare spiral of death dopo tab sospesa/frame lunghissimo;
- rendering una volta per frame, non una volta per simulation tick.

### Invariante

Una battaglia con stesso seed e stessi comandi deve avere lo stesso esito indipendentemente da refresh rate del display e timeScale.

---

## P0.3 — Sim Lab usa lo stesso tick

Eliminare il default indipendente `dt:0.05` come fonte di verità.

Dopo la scelta del tick canonico:

- esporre `CFG.FIXED_DT` o equivalente;
- Sim Lab usa quello come default;
- override `dt` resta disponibile solo per test diagnostici/timestep sensitivity.

---

## P0.4 — Intel pipeline

Situazione attuale: nello stesso `Simulation.update()` Intel viene ricalcolato in più punti.

Prima di ridurre le chiamate:

1. identificare chi legge Intel prima/dopo movimento;
2. identificare chi lo legge prima del ranged;
3. identificare chi richiede lo stato post-combat;
4. decidere se basta una singola snapshot per tick oppure se servono fasi dirty/cache.

Target: evitare computazioni duplicate senza cambiare semanticamente ciò che AI e ranged possono conoscere nello stesso tick.

---

## P0.5 — RNG del motore

Sostituire l'uso gameplay di `Math.random()` con RNG esplicito del runtime, per esempio:

- `State.rng.next()` oppure `Random.next()`;
- seed configurabile;
- seed salvato nei risultati Sim Lab;
- nessun monkey-patch globale di `Math.random` richiesto dal Sim Lab.

AdSense, UI e script esterni non devono essere influenzati dal seed della simulazione.

---

## P0.6 — Regression suite

Creare un set canonico di seed/scenari.

Controlli minimi:

- stesso seed ripetuto => stesso risultato e stesso stato finale significativo;
- reverse-order bias entro la soglia concordata;
- `stuck` non aumenta rispetto alla baseline;
- nessuna eccezione runtime;
- stessi risultati a x1/x2/x3;
- stesso tick di default nel browser e nel Sim Lab.

Le variazioni di win-rate causate dal nuovo timestep vanno registrate. Non vanno corrette con modifiche di bilanciamento nello stesso commit.

---

## Dopo P0

### P1 — consolidamento interno

- rimuovere lo state swap temporaneo di `State.terrain` in `Terrain.draw`;
- assorbire progressivamente i wrapper `legacy*` nelle implementazioni canoniche;
- eliminare patch/workflow one-shot.

### P2 — scaling

- cache/throttle Intel dove utile;
- selected panel dirty/throttled;
- i18n generato direttamente da key.

### P3 — pubblicazione

- CMP AdSense / verifica UE;
- security headers Vercel;
- README e metadata sito.

---

## Sequenza commit consigliata

1. `test: add timestep baseline matrix`
2. `fix: make language storage fail-safe`
3. `refactor: introduce canonical fixed simulation tick`
4. `refactor: align sim-lab default with canonical tick`
5. `perf: consolidate intel updates without semantic drift`
6. `refactor: inject seeded gameplay rng`
7. `test: add deterministic regression gates`

Ogni commit deve essere revertibile isolatamente.
