# Refactor tools

## Baseline timestep matrix

Apri la build del branch su `/play`, poi dalla console:

```js
await import('/tools/baseline-matrix.js')
```

Lo script carica automaticamente `sim-lab.js` se necessario.

### Baseline consigliata

```js
const report = await __COFFEE_BATTLES_BASELINE__.run({
  count: 300,
  seed: 1
})
```

Per una baseline più robusta:

```js
const report = await __COFFEE_BATTLES_BASELINE__.run({
  count: 500,
  seed: 1
})
```

Di default esegue gli stessi seed con:

- 20 Hz (`dt=0.05`)
- 30 Hz (`dt=1/30`)
- 60 Hz (`dt=1/60`)

Per ogni timestep esegue anche `reverseUnits:true` per il bias check.

### Esportazione

```js
__COFFEE_BATTLES_BASELINE__.downloadJSON()
```

oppure:

```js
copy(__COFFEE_BATTLES_BASELINE__.exportJSON())
```

Il report contiene sia le metriche aggregate sia una fingerprint compatta per ogni seed (`winner`, `simTime`, `stuck`, `timeout`, ruoli e collapse).

## Regola di lavoro

Non modificare timestep, RNG, Intel pipeline o bilanciamento prima di aver salvato almeno una baseline del commit di partenza.

Vedi `REFACTOR_P0.md` per la sequenza completa.
