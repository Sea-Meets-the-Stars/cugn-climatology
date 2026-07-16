# Initial exploration — CUGN climatology (2026 beta)

**Date:** 2026-07-15
**Data:** `$OS_SPRAY/CUGN/Climatology/2026 beta/` — 80 NetCDF files, 5.9 GB
**Source:** https://spraydata.ucsd.edu/products/cugn-climatology/new.php
**Explorer script:** `cugn_climatology/explore_2026beta.py` (writes `context/file_inventory.csv`)
**Provenance:** CF-1.9 / ACDD-1.3, Level-4 products from Scripps (Rudnick et al.),
`date_created` 2026-07-15 — freshly generated.

## 1. What the 80 files are

Each file name decodes as `{group}_{product}_{vcoord}_{line}.nc`:

- **group** — `lt` (long-term) or `st` (short-term). See §4; they are two
  different baseline periods, not two resolutions.
- **product** — one of five (see §3): `mean`, `annual_cycle`,
  `mean_annual_cycle`, `anomaly`, `total`.
- **vcoord** — vertical coordinate: `depth` (z) or `sigma` (potential density).
- **line** — CUGN section: `66`, `80`, `90` for `lt`; `56`, `66`, `80`, `90`,
  and `al` (alongshore) for `st`.

Counts (each product exists in both depth and sigma):

| group | lines | products | files |
|-------|-------|----------|-------|
| lt    | 66, 80, 90 (3)          | 5 | 3 × 5 × 2 = 30 |
| st    | 56, 66, 80, 90, al (5)  | 5 | 5 × 5 × 2 = 50 |
| **total** | | | **80** |

## 2. Grids and geometry

- **Cross-shore:** `distance` in km at 5 km spacing, starting at 0 **inshore**
  and increasing offshore. Each line has a different length / station count:

  | line | stations | length (km) | inshore (lat, lon) | offshore (lat, lon) |
  |------|----------|-------------|--------------------|---------------------|
  | 56 | 61  | 300 | 38.53, -123.27 | 37.17, -126.23 |
  | 66 | 81  | 400 | 36.89, -121.84 | 35.09, -125.71 |
  | 80 | 74  | 365 | 34.47, -120.48 | 32.83, -123.89 |
  | 90 | 107 | 530 | 33.50, -117.75 | 31.11, -122.61 |
  | al | 45  | 220 | 32.42, -119.96 | 34.13, -121.14 |

  (`al` is the alongshore line and runs roughly S→N rather than offshore.)
  `latitude`/`longitude` are 1-D coordinates along `distance`.

- **Vertical:** `depth` files have 50 levels, 10–500 m at 10 m spacing.
  `sigma` files have 21 levels of `potential_density` from 25.0 to 27.0
  kg m⁻³ at 0.1 spacing.

- **Time** (products that carry it): 10-day cadence.

## 3. The five products (and how they relate)

For a given group/line/vcoord:

| product | dims | meaning |
|---------|------|---------|
| `mean` | (depth, distance) | Time-independent mean field |
| `annual_cycle` | (time=365, depth, distance) | Daily climatological cycle, **anomaly form** (mean removed) |
| `mean_annual_cycle` | (time=365, depth, distance) | `mean + annual_cycle` (the full seasonal field) |
| `anomaly` | (time, depth, distance) | Interannual anomaly (10-day cadence) |
| `total` | (time, depth, distance) | The reconstructed observed field |

**Verified additive decomposition** (temperature, lt/depth/line 90, exact to
floating point):

```
total(t) = mean + annual_cycle[doy(t)] + anomaly(t)
mean_annual_cycle = mean + annual_cycle
```

So `mean`, `annual_cycle`, and `anomaly` are the three independent pieces;
`mean_annual_cycle` and `total` are conveniences derived from them. The
`annual_cycle` files span a nominal year (2007-01-10 → 2008-01-09, 365 days).

## 4. lt vs st — two baseline periods

Same variables and grids; they differ in the observational window used:

| group | `time_coverage` (mean) | anomaly/total time span |
|-------|------------------------|-------------------------|
| lt (long-term)  | 2007-01-01 → 2014-01-01 | 2006/2007 → 2026 |
| st (short-term) | 2017-01-01 → 2025-01-01 | 2017/2019/2020 → 2026 |

The two means differ meaningfully — e.g. line 90 temperature is on average
**+0.23 °C warmer** in `st` than `lt` (max local difference ~1.05 °C),
consistent with recent warming relative to the earlier baseline. **Open
question for you (see Q&A): confirm the intended lt/st definitions and how you
want anomalies referenced.**

The anomaly/total records start at different years per line (data availability):
lt line 66 begins 2007, lines 80/90 begin 2006; st line 56 begins 2020, `al`
begins 2019, lines 66/80/90 begin 2017.

## 5. Variables

**The variable set differs between `st` and `lt` — this is the key correction
to my first pass** (which only inspected `lt` line 90 and wrongly concluded
there was no oxygen). Verified by scanning all 80 files
(`scratchpad`-driven, now folded into the exploration):

Common to both groups (all products, both vcoords): `temperature` (°C),
`salinity` (PSS-78), `chlorophyll_a` (mg m⁻³), `sigma_t` (kg m⁻³),
`potential_temperature`, `geostrophic_velocity` (m s⁻¹),
`doppler_velocity_along`, `doppler_velocity_across`.

**Present only in the `st` (short-term) files — all 50 of them:**

- `doxy` — Dissolved Oxygen Molar Concentration
  (`mole_concentration_of_dissolved_molecular_oxygen_in_sea_water`)
- `acoustic_backscatter`

**So dissolved oxygen IS in the 2026 beta — in the short-term products.** It is
absent from every `lt` file. This is physically sensible: dissolved-oxygen and
acoustic-backscatter sensors became standard on the gliders more recently, so
the 2007–2014 long-term baseline predates reliable coverage while the 2017–2025
short-term period has it. (This answers your Q&A note "I expect DO to be
present.")

Other per-file variations:

- `potential_density` appears only in the `mean` and `mean_annual_cycle`
  products (depth coord). The `annual_cycle`, `anomaly`, and `total` products
  omit it — it is not carried as an anomaly quantity — and the sigma files omit
  it because it is (essentially) the vertical coordinate.
- `chlorophyll_a` is dropped from the `mean_sigma` files specifically (present
  in every other product/coord combination).

The full variable-by-file matrix is in `context/file_inventory.csv`
(`vars` column, one row per file).

## 6. Initial figures

Generated by `cugn_climatology/figs_initial.py` (writes to `context/figs/`):

| Figure | What it shows |
|--------|---------------|
| `fig01_line_geometry.png` | Map of the 5 section lines; 56 is northernmost, 90 off San Diego, `al` bridges 80↔90. Filled circle marks the inshore (distance = 0) end. |
| `fig02_mean_sections_st90.png` | Short-term mean cross-sections (T, S, DO, chl-a) on Line 90, depth coords. Shows warm stratified surface, fresher offshore surface, a subsurface chlorophyll max, and a clear oxygen-minimum layer at depth inshore. |
| `fig03_mean_sigma_st90.png` | Mean temperature on potential-density coordinates (Line 90). |
| `fig04_annual_cycle_sst.png` | Seasonal cycle of 10 m temperature vs distance (Line 90): warm late-summer/autumn surface, cool spring. |
| `fig05_anomaly_hovmoller.png` | Interannual 10 m temperature anomaly (time × distance), 2017–mid-2026. Coherent warm/cool phases; strong warm anomaly at the end of the record. |
| `fig06_lt_vs_st_mean.png` | st − lt mean temperature (Line 90): coherent surface-intensified warming (~0.75 °C near-surface, decaying with depth). |

The near-shore white stripes in the depth sections are shallow-bathymetry
stations with no deep bins (expected, not a data error).

## 7. Data coverage / gaps

- NaN fraction in the `mean` fields is ~4–6 % (deep/offshore corners the
  gliders don't reach; Doppler velocities slightly higher at 6.2 %).
- The `total`/`anomaly` time axes are **padded to the end of 2026**: for
  lt_total line 90, data are valid from 2006-10-28 through **2026-07-10**, and
  every 10-day step after that (through 2026-12-27) is entirely NaN. The last
  valid step (2026-07-10) matches today's date — this is a live/rolling product
  with placeholder slots for the rest of the year.

## Resolved (from Q&A, 2026-07-15)

1. **lt vs st intent:** Confirmed — long-term (2007–2014) vs short-term
   (2017–2025) baselines.
2. **Scope:** all lines, both vertical coordinates, all variables.
3. **Oxygen:** you expected DO to be present — and it **is**, in the 50 `st`
   files (see §5). My first-pass "no DO" claim was an artifact of only checking
   `lt` line 90. Corrected.

## New open questions (also in download.md Q&A)

1. **DO / backscatter in lt:** Is it expected/acceptable that dissolved oxygen
   and acoustic backscatter exist **only** in the short-term files (the
   long-term 2007–2014 baseline predates routine sensors)? If the climatology
   needs a long-term DO field, that will require a different approach.
2. **Chlorophyll-a on density coords:** `chlorophyll_a` is dropped from the
   `mean_sigma` files but kept in every other product/coord — intentional?
3. **End-of-record padding:** the `total`/`anomaly` axes carry all-NaN 10-day
   slots after 2026-07-10 (today). Should downstream code trim these, or do you
   want them retained as placeholders for the rolling product?
