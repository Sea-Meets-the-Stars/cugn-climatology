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

Depth files carry 9 variables; sigma files carry 7 (no separate
`potential_density`, and `mean_sigma` drops `chlorophyll_a`):

`temperature` (°C), `salinity` (PSS-78), `chlorophyll_a` (mg m⁻³),
`sigma_t` (kg m⁻³), `potential_density` (depth only), `potential_temperature`,
`geostrophic_velocity` (m s⁻¹), `doppler_velocity_along`,
`doppler_velocity_across`.

Note: `annual_cycle` and `anomaly` files omit `potential_density` (it is not an
anomaly quantity); `mean` and `mean_annual_cycle` keep it. There is **no
dissolved-oxygen variable** in these files, unlike the older `.parquet`/`.npz`
`doxy_*` products in `$OS_SPRAY/CUGN/`.

## 6. Data coverage / gaps

- NaN fraction in the `mean` fields is ~4–6 % (deep/offshore corners the
  gliders don't reach; Doppler velocities slightly higher at 6.2 %).
- The `total`/`anomaly` time axes are **padded to the end of 2026**: for
  lt_total line 90, data are valid from 2006-10-28 through **2026-07-10**, and
  every 10-day step after that (through 2026-12-27) is entirely NaN. The last
  valid step (2026-07-10) matches today's date — this is a live/rolling product
  with placeholder slots for the rest of the year.

## Open questions (also in download.md Q&A)

1. **lt vs st intent:** Are "long-term" and "short-term" the right reading
   (2007–2014 vs 2017–2025 baselines)? Which should the climatology work treat
   as primary?
2. **Scope of the climatology work:** which lines, which vertical coordinate
   (depth vs sigma), and which variables are the focus?
3. **Oxygen:** should dissolved oxygen be part of this climatology (it is
   absent from the 2026 beta NetCDFs but present in older CUGN products)?
