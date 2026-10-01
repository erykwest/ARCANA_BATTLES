# P0.5 — Explicit gameplay RNG validation

Branch di lavoro: `refactor/p0-rng`

Engine RNG commit: `21f15b7`

## Change

La casualità gameplay non dipende più direttamente da `Math.random()`.

Il motore espone ora un runtime-owned `Random` con:

- `Random.next()` come unica API gameplay;
- `Random.setSeed(seed)` con lo stesso algoritmo `mulberry32` usato in precedenza dal Sim Lab;
- `Random.useSystem()` per il normale gioco browser non seedato;
- `Random.capture()` / `Random.restore()` per isolare una simulazione seedata e ripristinare la sorgente precedente.

Sono state migrate 24 chiamate gameplay da `Math.random()` a `Random.next()`.

Il Sim Lab v0.3 non monkey-patcha più `Math.random` globale. In `beginRuntime()` imposta il seed sul motore con `Random.setSeed(o.seed)` e in `endRuntime()` ripristina lo stato RNG precedente.

AdSense, UI, browser code e script esterni non vengono quindi più influenzati dal seed della simulazione.

## Static verification

Nel file `COFFEE_BATTLES.html` non resta alcuna chiamata `Math.random()` gameplay.

L'unico riferimento residuo a `Math.random` è `Random._systemSource`, usato come sorgente non deterministica quando il motore non è in modalità seedata.

## Canonical regression

I fingerprint canonici 30 Hz sono stati confrontati contro P0.4.

### Seed 1

- winner: RED
- simTime: 145.433 s
- expected SHA-256: `566a3ed07a224101004343c8b5b7d6f5bdb0a31d74fbf181b2a033eb6fa5e8f6`
- actual SHA-256: identical
- result: **PASS**

### Seed 2 — long case

- winner: RED
- simTime: 268.567 s
- expected SHA-256: `09c9c11b55e3d76f5a2943bcdab2d5576ec41308ca70c73a0bdc784d23e94c73`
- actual SHA-256: identical
- result: **PASS**

### Seed 5 — battle-limit case

- winner: BLUE
- simTime: 600 s
- expected SHA-256: `1777188bcd75fdf0ebbe364a4553fa1820052213c03b9f7d101c255aaaa9f677`
- actual SHA-256: identical
- result: **PASS**

## Outcome

**P0.5 PASS.**

Il determinismo è ora una proprietà esplicita del runtime di COFFEE BATTLES invece di dipendere da un monkey-patch globale del Sim Lab.

Next P0 item: consolidare i gate esistenti in una regression suite permanente e leggera (P0.6), evitando workflow one-shot e timeout inutilmente lunghi.
