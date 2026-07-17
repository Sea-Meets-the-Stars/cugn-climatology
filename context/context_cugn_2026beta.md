# Context: the CUGN "2026 beta" climatology — data, code, config, and web

**Purpose.** This document is a complete, implementation-oriented description of
how the CUGN 2026 beta climatology is produced, from Level-3 glider input to the
NetCDF products, the pre-rendered figures, and the website. It is intended to
guide a Python re-implementation/extension in this repository.

**Source material examined** (all under `$OS_SPRAY/CUGN/Climatology/Original/`,
where `$OS_SPRAY = /home/xavier/Projects/Oceanography/data/Spray/`):

| Path | What it is |
|------|------------|
| `config/*.json` | 12 JSON files driving the MATLAB→NetCDF export |
| `src_231/*.m` | ~70 MATLAB functions — the generation pipeline |
| `2006/` | Long-term (`lt`) run: `nc/` outputs + `plots/66/` figures |
| `2017/` | Short-term (`st`) run: `nc/` outputs only (no plots provided) |
| `web/cugn-climatology/` | `new.php` + `assets/catalog2026.js` — the website |

> The MATLAB `.mat` inputs (`anncycXX.mat`, `mapXX.mat`) and the Level-3
> combined-mission source are **not** on this laptop. Per project decision, the
> pipeline is documented as-designed (from code inspection); it is not run here.

---

## 1. The two runs: `lt` (2006) and `st` (2017)

The 2026 beta is two independent runs, distinguished by baseline period and
driven by two wrapper scripts:

| Run | Dir | Driver | Lines | Variables | Oxygen? |
|-----|-----|--------|-------|-----------|---------|
| **long-term (`lt`)** | `2006/` | `wrapcugn_2006.m` | 66.7, 80.0, 90.0 | t, s, fl, abs, udop, vdop | **no** |
| **short-term (`st`)** | `2017/` | `wrapcugn_2017.m` | 56.7, 66.7, 80.0, 90.0, along | t, s, fl, abs, udop, vdop, **oxumolkg** | **yes** |

`wrapcugn_2017.m` adds `oxumolkg` (dissolved oxygen) to the variable list — this
is the definitive reason **DO and acoustic backscatter appear only in the `st`
NetCDF files**. The mean baseline windows recorded in the shipped NetCDF
`time_coverage_*` attributes are **lt: 2007–2014** and **st: 2017–2025**.

Both drivers call `updateclim` (rolling update) then `allanommap` (builds all
derived products) and save `mapXX.mat` per line.

---

## 2. Products and their MATLAB sources

There are **5 products × 2 vertical coordinates = 10 product configs**, each a
JSON in `config/`. Each names the MATLAB `.mat` source variable it exports.
Note the naming subtlety: the NetCDF `annual_cycle` is the **mean-removed**
seasonal cycle, while `mean_annual_cycle` is the **full** seasonal field.

| NetCDF product | title | source `.mat` | source variable | dims |
|----------------|-------|---------------|-----------------|------|
| `mean_depth` | Mean | `anncycXX.mat` | `meanmaptm` | (depth, dist) |
| `mean_sigma` | Mean | `anncycXX.mat` | `meanmapsig` | (sigma, dist) |
| `annual_cycle_depth` | Annual Anomaly | `anncycXX.mat` | `avmapnomeantm` | (time=365, depth, dist) |
| `annual_cycle_sigma` | Annual Anomaly | `anncycXX.mat` | (sigma variant) | (time=365, sigma, dist) |
| `mean_annual_cycle_depth` | Annual Cycle | `anncycXX.mat` | `avmaptm` | (time=365, depth, dist) |
| `mean_annual_cycle_sigma` | Annual Cycle | `anncycXX.mat` | (sigma variant) | (time=365, sigma, dist) |
| `anomaly_depth` | Interannual Anomaly | `mapXX.mat` | `anommaptmem` | (time, depth, dist) |
| `anomaly_sigma` | Interannual Anomaly | `mapXX.mat` | `anommapsigem` | (time, sigma, dist) |
| `total_depth` | Total | `mapXX.mat` | `maptmem` | (time, depth, dist) |
| `total_sigma` | total | `mapXX.mat` | `mapsigem` | (time, sigma, dist) |

Additive relationship (holds by construction; verified in the NetCDFs to
machine precision): **`total = mean + annual_cycle[doy] + anomaly`**, and
`mean_annual_cycle = mean + annual_cycle`.

Suffix decoder for the MATLAB variable names (from `allanommap.m`):
`tm` = topography-masked (`topomask`), `em` = error-masked (`errmask`) +
date-masked (`datemask`), `sig` = interpolated to density surfaces
(`interpmap_sigma`). The shipped products are the fully-masked `*tmem` / `*sigem`
variants.

---

## 3. Grids and coordinates

- **Cross-shore `distance`**: 0 (inshore) → offshore, step **dx = 5 km**.
  Per-line extent (from `allanncyc_var_split.m`): 90 → 530 km, 80 → 365 km,
  66 → 400 km, 56 → 300 km, along → 220 km.
- **Depth**: 10–500 m, step **10 m** (50 levels).
- **Potential density `sigma`** (sigma-coord products): **25.0–27.0**, step
  **0.1** (21 levels), set by `sigsig = 25:0.1:27`.
- **Time**: 10-day cadence (`dt = 10`), encoded as **Unix seconds since
  1970-01-01** in the NetCDF. The `annual_cycle`/`mean_annual_cycle` products
  use a nominal 365-day year (2007 as the reference year, see
  `anncyc2avmap_var.m`).
- `latitude`/`longitude` are 1-D along `distance`, from `do2ll` given the line
  endpoints.

---

## 4. The processing pipeline (step by step)

### 4.1 Input — Level-3 combined missions
`combineMissions_var_split(line, vars, yearstart, yearend)` assembles quality-
controlled, depth-binned glider CTD/ADCP/oxygen data into a `ctd` struct
(fields: `t, s, fl, abs, udop, vdop, oxumolkg, u, v`, plus `dist, offset, time,
depth`, and along-line endpoints). Not present on this laptop.

### 4.2 Annual cycle `A` — Gaussian-weighted harmonic fit
`annualcycleg_var.m` / `annualcycleg_var_covm.m` fit, at every depth level and
cross-shore bin, a harmonic model in time:

```
y(t) = c0 + Σ_{k=1..K} [ a_k sin(kωt) + b_k cos(kωt) ],   ω = 2π/365.25 d,  K = maxharmonic = 3
```

- Fit is **weighted least squares** with a **Gaussian cross-shore window**
  (`W = exp(-((dist - xcenter)/xwidth)²)`, `xwidth = 15 km`), using only years
  `yearstart..yearend` (`winmin = 1e-3` truncates the window).
- Stored in `anncycXX.mat` as struct `A` with fields per variable:
  `constant` (nlev × nbin), `sin`/`cos` (nlev × nbin × K); the `_covm` variant
  also stores the coefficient covariance `covm` for error propagation.
- `A.constant` **is the time-mean** (the k=0 term).
- Evaluate anywhere with `anncycinterp(A, var, level, time, dist)` (harmonic
  synthesis + linear interpolation in cross-shore between bins).

Product structures derived from `A` (see `allanncyc_var_split.m`):
- `meanmap` = `A.constant`, + derived vars → **mean** product (`meanmaptm`).
- `avmap` = full cycle evaluated daily for 2007 (365 steps) → **mean_annual_cycle**
  (`avmaptm`).
- `avmapnomean` = `avmap − meanmap` → **annual_cycle** (mean-removed;
  `avmapnomeantm`).
- Sigma variants via `interpmap_sigma`; `demeanmap` splits mean/anomaly on
  density surfaces.

### 4.3 Objective mapping of interannual anomalies
`climatologyCCS_New.m` (driver `runclim_New.m`) produces the interannual
anomaly maps `anommap` by **objective analysis (Gauss–Markov / OI)**:

- For each variable and depth level: subtract the annual cycle
  (`anncycinterp`), then map the residual onto the (distance × time) grid.
- **Gaussian covariance** `C(r,s) = exp(-r²/Lx² - s²/Lt²)` with **Lx = 30 km**,
  **Lt = 60 days**; **noise/signal = 0.1**; grid `dx = 5 km`, `dt = 10 d`.
- `computeCovMtrx.m` builds the sparse data–data (`A`) and model–data (`B`)
  covariance matrices (thresholded at `covmin = 1e-3`);
  `generateHovMap_AnomOnly.m` solves `map = B (A⁻¹ d)` and the mean-square error
  `mse = 1 - Σ B'·(A⁻¹B') / amp`.
- Projection thresholds: `mindistthresh = -5 km`; across-line
  `maxoffthresh = 90 km` for lines **80 and 90** (∞ for 56/66).
- ADCP note: `abs(1,:)` (surface bin) set NaN; `udop/vdop` surface bin NaN for
  years ≤ 2013 (750 kHz→1 MHz ADCP change in 2013).
- Output `anommap` (+ `err`) saved to `map_XX_AnomOnly.mat`.

### 4.4 Assembling all products
`allanommap.m` combines `anommap` with `avmap`:
- `map = anommap2map(anommap, avmap)` — adds the annual cycle back → **total**.
- `addderivedvars(map)` — computes derived fields (below).
- Masking: `maptm = topomask(map)`, `maptmem = datemask(errmask(maptm, 0.3))`.
- `anommap = map2anommap(...)`, masked identically → **anomaly** products.
- `mapsig = interpmap_sigma(maptm, 25:0.1:27)` → sigma-coordinate products.

### 4.5 Derived variables (`addderivedvars.m`) — **EOS-80**, not TEOS-10
Uses the **`sw_*` seawater toolbox** (EOS-80). This matters for the Python port
(match with `seawater`/`gsw` care):
- `p = sw_pres(depth, lat)`
- `theta = sw_ptmp(s, t, p, 0)` → `potential_temperature`
- `rho = sw_dens(s, t, p) - 1000` → `sigma_t`
- `sigma = sw_pden(s, t, p, 0) - 1000` → `potential_density`
- `geov = computeGeoV(...)` (thermal-wind geostrophic velocity)
- `ox = oxumolkg2ox(oxumolkg, s, t, p)` (µmol/kg → mL/L style)
- `rotateuv` rotates currents to along/cross-shore using the line endpoints.

### 4.6 Masking (defines NaN patterns in the products)
- **`topomask.m`** — sets values below the bottom to NaN using per-line
  bathymetry (`topoXX.mat`). *This is the origin of the near-shore white
  stripes in depth sections.*
- **`errmask.m`** — OI error > **`errthresh = 0.3`** → NaN. Derived
  (theta/rho/sigma/geov) masked by `max(err_t, err_s)`; oxygen by
  `max(err_t, err_s, err_ox)`.
- **`datemask.m`** — masks time steps outside each line's valid window. **Per-line
  start dates** (explains the different record starts seen in the anomaly/total
  products): 66 → 2007-04-20, 80 → 2006-02-26, 90 → 2006-10-20,
  along → 2019-01-01, 56 → 2019-12-13; end = `config.timestamp` (run time).

### 4.7 Rolling update (`updateclim.m`)
The climatology is a **rolling product**: it goes `ndays = 730` back, recomputes
the OI over that window, and splices the new half (`ndays/2`) onto the retained
history. `config.timelastctd` records the last CTD time. This is why the shipped
`total`/`anomaly` axes are padded to end-of-year with trailing all-NaN steps
after the last valid date.

---

## 5. Canonical parameters (project reference)

Recorded from `climatologyCCS_New.m`, `annualcycleg_var_covm.m`,
`allanncyc_var_split.m`, and the masking functions:

| Parameter | Value | Meaning / source |
|-----------|-------|------------------|
| `Lx` | 30 km | OI cross-shore length scale |
| `Lt` | 60 days | OI time length scale |
| `dx` | 5 km | map cross-shore resolution |
| `dt` | 10 days | map temporal resolution |
| `noise` | 0.1 | OI noise/signal ratio |
| `covmin` | 1e-3 | covariance truncation |
| `maxharmonic` (K) | 3 | annual + 2 harmonics; ω = 2π/365.25 d |
| `xwidth` | 15 km | Gaussian window e-folding (annual-cycle fit) |
| `winmin` | 1e-3 | window truncation (annual-cycle fit) |
| `errthresh` | 0.3 | OI error mask threshold |
| `mindistthresh` | −5 km | min along-line distance for projection |
| `maxoffthresh` | 90 km (lines 80/90; ∞ for 56/66) | max across-line offset |
| `sigsig` | 25:0.1:27 | density surfaces (21 levels) |
| `ndays` | 730 | rolling-update lookback |
| depth grid | 10–500 m × 10 m | 50 levels |

---

## 6. Config files (`config/*.json`)

- **`globals.json`** — CF-1.9 / ACDD-1.3 global attributes applied to every
  NetCDF: institution (Scripps IDG), reference (Rudnick, Zaba, Todd & Davis
  2016, *Prog. Oceanogr.*), DOI `10.21238/S8SPRAY7292`, processing level
  ("Level 4 … from level 3 binned glider data"), license, keywords,
  contributors, and 5 km / 10 m resolution metadata. `date_created`/geospatial
  bounds are filled at export time.
- **`variables.json`** — canonical per-variable definitions and the
  **MATLAB→NetCDF name map** (`matvarname`): `t`→temperature,
  `s`→salinity, `fl`→chlorophyll_a, `rho`→sigma_t, `sigma`→potential_density,
  `theta`→potential_temperature, `geov`→geostrophic_velocity,
  `udopalong/udopacross`→doppler_velocity_along/across, `abs`→acoustic_backscatter,
  `oxumolkg`→doxy. Carries CF `standard_name`, `units`, `coordinates`,
  `cell_methods`, comments (e.g. T is ITS-90; doppler velocities are
  coast-oriented, not true N/E).
- **Product configs** (`{mean,annual_cycle,mean_annual_cycle,anomaly,total}_{depth,sigma}.json`)
  — each has a `data_product` block (source `.mat` file + variable +
  dimensions + name maps) and `nc_dimensions`/`nc_variables` blocks that define
  the output dims/vars and any per-product attribute overrides (e.g.
  `cell_methods: "time: mean over years"` on the mean products). The export code
  reads these to write CF-compliant NetCDF.

---

## 7. NetCDF output conventions

- CF-1.9 / ACDD-1.3, `cdm_data_type = Grid`.
- `doxy` **units are `micromol kg-1` (per-mass)** despite the `long_name`
  "Dissolved Oxygen Molar Concentration" — a metadata wording mismatch to flag
  upstream.
- `acoustic_backscatter` is uncalibrated ADCP dB (note the 2013 frequency
  change; st period is uniformly post-2013).
- Time as Unix seconds; `mean`/`mean_sigma` have no time dimension.
- `chlorophyll_a` is listed in the `mean_sigma` config name-map but does not
  survive to the `mean_sigma` NetCDF output (density-surface mean drops it) —
  a config-vs-output discrepancy worth noting.

---

## 8. Pre-rendered figures (`2006/plots/66/`)

Only the **`lt` run, line 66** figures are present (~27,474 PNGs). The `st`
(2017) plots and other lines are **not** provided. Generated by
`wrapcugnplots_2006.m` → `wrapperanomplots.m` / `wrapperavplots.m` and the
`make*plots*.m` family. Subdirectories = product/plot types:

| Subdir | Content |
|--------|---------|
| `meanmap`, `meanmapsig` | mean cross-sections (depth / density) |
| `avmap`, `avmapsig` | full annual-cycle fields |
| `avmapnomean`, `avmapsignomean` | mean-removed annual cycle |
| `map`, `mapsig` | total fields (per time / Hovmöller) |
| `anommap`, `anommapsig` | interannual anomaly (many σ/depth × distance slices) |
| `seasons` | seasonal composites |

Filename pattern: `<line>_<plottype>_<axis>_<var>[_<qualifier>].png`, e.g.
`66_meanmap_xz_t.png`, `66_xz_t_summer.png`,
`66_anommapsig_time_t_25.5_100.png` (σ-surface 25.5, 100 km). Variable tokens
are the MATLAB names (`t, s, fl, rho, sigma, theta, geov, abs, udopalong,
udopacross, oxumolkg, depth`).

---

## 9. Website (`web/cugn-climatology/`)

- **`new.php`** (1232 lines) — the 2026 beta page. Two parts:
  1. An **interactive figure explorer** (up to 4 figure panels,
     `Figure1..Figure4`) with a Settings panel whose controls are
     `experiment`/`baseline` (lt vs st), `variable`, `plot`, `dimension`
     (depth vs density), `projection`, and up to two `subset` selectors
     (e.g. σ-surface, distance). Selections map to one of the pre-rendered PNGs.
  2. A **Data Access** section listing every NetCDF for download (the same 80
     files catalogued in `context/initial_exploration.md`).
- **`assets/catalog2026.js`** (1837 lines) — client logic:
  `loadSizes()` fetches `assets/file_info2026.json` (per-file sizes +
  `file_update_time`, generated daily by a Python script), `loadTimes()` fetches
  time-axis JSONs, and `setFigOptions()` builds the dropdown option tree
  (`figsOptions`, `xz_*` time lists) that resolves a settings combination to a
  figure path.
- Implication: the website is **static PNG + JSON driven** — no server-side
  computation. A Python re-implementation must either reproduce the PNG naming
  scheme or replace the explorer with dynamic (e.g. server/notebook) rendering.

---

## 10. Guidance for the Python port

1. **Two-stage decomposition is the core.** Stage 1: Gaussian-windowed harmonic
   annual cycle (`A`); Stage 2: OI of the residual interannual anomaly. A naive
   day-of-year climatology (as in this repo's `climatology.py`) approximates the
   *mean* and *annual cycle* well but **cannot reproduce the OI-smoothed
   anomalies** — port `computeCovMtrx` + `generateHovMap_AnomOnly` for fidelity.
2. **Match the equation of state.** The MATLAB uses **EOS-80 (`sw_*`)**. Decide
   whether to reproduce EOS-80 exactly (use `python-seawater`) or migrate to
   TEOS-10 (`gsw`) and document the offset.
3. **Reproduce the three masks** (topo, err≤0.3, per-line date windows) — they
   define the NaN structure and the per-line record starts.
4. **Respect the parameter set in §5** (the user has approved recording these as
   canonical for now).
5. **Config-driven export.** The JSON configs already encode the entire
   NetCDF schema and MATLAB→NetCDF mapping; a Python exporter can consume them
   directly rather than re-encoding attributes.
6. **Rolling update semantics** (§4.7) — decide whether the Python product is
   a rolling or fixed-window climatology.

## 11. Key files reference

| Concern | File(s) |
|---------|---------|
| Run drivers | `wrapcugn_2006.m` (lt), `wrapcugn_2017.m` (st) |
| Annual cycle | `annualcycleg_var.m`, `annualcycleg_var_covm.m`, `anncycinterp.m`, `allanncyc_var_split.m` |
| Objective mapping | `climatologyCCS_New.m`, `runclim_New.m`, `computeCovMtrx.m`, `generateHovMap_AnomOnly.m`, `generateGrid.m` |
| Product assembly | `allanommap.m`, `anommap2map.m`, `map2anommap.m`, `anncyc2avmap_var.m`, `anncyc2meanmap_var.m`, `demeanmap.m`, `demeanavmap.m`, `interpmap_sigma.m` |
| Derived vars | `addderivedvars.m`, `computeGeoV.m`, `rotateuv.m`, `do2ll.m` |
| Masking | `topomask.m` (+ `topoXX.mat`), `errmask.m`, `datemask.m` |
| Rolling update | `updateclim.m`, `prunectd.m` |
| Config | `config/globals.json`, `config/variables.json`, `config/*_{depth,sigma}.json` |
| Plots | `wrapcugnplots_2006.m`, `wrapperanomplots.m`, `make*plots*.m` |
| Web | `web/cugn-climatology/new.php`, `assets/catalog2026.js`, `assets/file_info2026.json` |

## 12. Known gotchas

- `doxy` long_name vs per-mass units mismatch (§7).
- `chlorophyll_a` absent from `mean_sigma` output despite the config name-map (§7).
- DO / acoustic backscatter exist only in `st` (§1).
- Near-shore white stripes = `topomask`, not missing data (§4.6).
- Trailing all-NaN time steps = rolling-product padding (§4.7); trim before use.
- EOS-80 vs TEOS-10 (§4.5).
- `allanncyc_var_split.m` carries per-line `yearstart` (56/along later than
  66/80/90) and a `yearend` parameter; the authoritative baseline windows are
  the NetCDF `time_coverage_*` attributes (lt 2007–2014, st 2017–2025).
