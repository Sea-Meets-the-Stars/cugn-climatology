# Context for the CUGN Climatology project

This prompt doc will build the context for the CUGN Climatology project.
We will examine data, code, and config files that were used to generate the `2026 beta` climatology.  We will then generate a context file describing the data, code, and config files called `context/context_cugn_2026beta.md`.

## Process

If you need to run Python, use the "ocean14" conda environment.

## Data

- There are a set of JSON config files at `$OS_SPRAY/CUGN/Climatology/Origynal/config/` that were used to generate the `2026 beta` climatology.
- There is a large set of PNG figures in `$OS_SPRAY/CUGN/Climatology/Original/2006/plots/66/` that are currently used for the website.
- The file `$OS_SPRAY/CUGN/Climatology/Original/web/cugn-climatology/new.php` is the source for the `2026 beta` climatology website.
- The folder `$OS_SPRAY/CUGN/Climatology/Original/src_231/` contains the MATLAB code that was used to generate the `2026 beta` climatology.

## Prompts

1, Examine the data, code, and config files described in the `Data` section above.  Ask me a set of questions in the Q&A section below before writing the context file.  Log your work in the Logs section.  Use Fable if you can.

2. I have answered the questions in the Q&A section.  Please check my answers.  Continue your work and create the context file.  Log your work in the Logs section.  Use Fable if you can.

3. I have downloaded the Rudnick et al. 2017 reference paper and put it in `context/rudnick2017.pdf`.  Please read it and add what you learn to the context file.  Log your work in the Logs section.  Use Fable if you can.

## Q&A

I examined the config, MATLAB source, plots, and website source. Before writing
`context/context_cugn_2026beta.md`, a few questions:

**1. Purpose & depth of the context file.** Is it primarily a reference for
*reproducing/extending* the climatology in Python (this repo's goal), or a
higher-level orientation to what the 2026 beta is? Concretely: do you want a
function-by-function walkthrough of the `src_231` MATLAB pipeline, or a
methodology-level summary (annual-cycle harmonic fit → objective mapping →
masked derived products → NetCDF) with pointers to the key files?
>A. Be comprehensive and detailed.  The context file should be a complete description of the data, code, and config files.  You will use it to guide the development of the Python code in this repo.

**2. Missing MATLAB inputs.** The `src_231` code loads `anncycXX.mat`,
`mapXX.mat`, and Level-3 combined-mission data (`combineMissions_var_split`),
but **none of those `.mat` inputs are on this laptop** (only the code, config,
NetCDF outputs, and 2006 plots are). I can document the pipeline from code
inspection, but I can't run it here. Is retrieving those inputs in scope, or
should the context file document the pipeline as-designed only?
>A. You will not need to run the MATLAB code.  You will only need to document the pipeline as-designed.

**3. Missing st plots; only line 66.** The prompt points to
`Original/2017/plots/66/`, but **2017 has no plots at all (0 PNGs)** — only
`2006/plots/66/` exists (~27,500 PNGs across product subdirs: anommap, avmap,
map, meanmap, seasons, and their `sig` variants). Also only **line 66** has
plots. Is that expected (66 as the exemplar), or are the st / other-line plots
supposed to be present?
>A. My mistake.  There were no plots for the 2017 data provided.

**4. Confirm baseline mapping.** I read **2006 = long-term (lt)** (lines
66/80/90, no oxygen) and **2017 = short-term (st)** (lines 56/66/80/90/along,
with oxygen), matching `wrapcugn_2006.m` / `wrapcugn_2017.m`. Correct? And what
exact baseline year ranges should the context file cite for each annual-cycle
`A` (shipped attrs imply lt mean 2007–2014, st mean 2017–2025)?
>A. Yes, that is correct.

**5. Website mechanics — in scope?** Should the context file document how the
site serves the products (`new.php` + `assets/catalog2026.js` +
daily-generated `file_info2026.json`, with interactive figures driven by JS),
or focus only on the scientific data/code/config and leave the web layer out?
>A. Yes, the context file should document the website mechanics.

**6. Canonical parameters.** Should I record these mapping/annual-cycle
parameters (from `climatologyCCS_New.m` and `annualcycleg_var_covm.m`) as the
project's canonical config: objective-map length scales **Lx = 30 km,
Lt = 60 days**; grid **dx = 5 km, dt = 10 days**; **noise/signal = 0.1**;
**maxharmonic = 3** (annual + 2); error mask **errthresh = 0.3**; across-line
offset threshold **90 km** for lines 80/90 (∞ for 56/66); rolling update
**ndays = 730**?
>A. I think so.  Please do so for now

## Logging

Append an entry to the **Logs** section of this file using the format:

```
### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>
```

## Logs

### 2026-07-17 (Examined the 2026 beta source data/code/config; asked questions)

Surveyed all sources under `$OS_SPRAY/CUGN/Climatology/Original/` to prepare for
writing `context/context_cugn_2026beta.md`. Did not write the context file yet
(per the prompt, asked questions first — see Q&A above).

**Config (`config/*.json`, 12 files).**
- `globals.json` — CF-1.9/ACDD-1.3 global attributes (Scripps IDG, Rudnick et
  al. 2016 reference, DOI 10.21238/S8SPRAY7292, 5 km horizontal / 10 m vertical
  resolution).
- `variables.json` — canonical variable definitions and the **MATLAB→NetCDF
  name map** (e.g. `t`→temperature, `s`→salinity, `fl`→chlorophyll_a,
  `rho`→sigma_t, `sigma`→potential_density, `theta`→potential_temperature,
  `geov`→geostrophic_velocity, `udopalong/udopacross`→doppler velocities,
  `abs`→acoustic_backscatter, `oxumolkg`→doxy).
- 10 product configs (`{mean,annual_cycle,mean_annual_cycle,anomaly,total}_{depth,sigma}.json`)
  — each names its MATLAB source file + variable and its NetCDF dims/attrs, e.g.
  `mean_depth` ← `anncycXX.mat:meanmaptm`, `total_depth` ← `mapXX.mat:maptmem`;
  time encoded as Unix seconds (matches the observed NetCDF time axes).

**MATLAB pipeline (`src_231/`, ~70 `.m` files).** Reconstructed the flow:
1. `annualcycleg_var_covm.m` — annual cycle `A` per line: **maxharmonic = 3**
   (annual + 2) harmonic fit at period 365.25 d with a Gaussian cross-shore
   window; stored in `anncycXX.mat` (with `avmap`, `avmapsig`).
2. `climatologyCCS_New.m` — **objective mapping** (Gaussian covariance OI):
   Lx = 30 km, Lt = 60 d, dx = 5 km, dt = 10 d, noise = 0.1; removes the annual
   cycle then maps anomalies + error maps. Offset threshold 90 km for lines
   80/90.
3. `allanommap.m` — derives all products from `anommap` + `avmap`: `map` (add
   cycle back = total), `topomask` (bathymetry), `errmask` (errthresh = 0.3),
   `datemask` (temporal), sigma interpolation (`interpmap_sigma`, σ 25:0.1:27).
   The masked variables (`maptmem`, etc.) are exactly the NetCDF products.
4. `updateclim.m` — rolling update (ndays = 730 back, splice) — this is the
   mechanism behind the padded/rolling end-of-record I saw in the NetCDFs.
- **lt vs st drivers:** `wrapcugn_2006.m` (lt: lines 66/80/90, vars t,s,fl,abs,
  udop,vdop — **no oxygen**) vs `wrapcugn_2017.m` (st: lines 56/66/80/90/along,
  **adds oxumolkg**). This is the definitive reason DO is st-only.
- Key insight: the shipped products come from **objective analysis**, not a
  plain harmonic reconstruction — this explains why recomputing from the 10-day
  `total` (my §9 climatology.py) only approximates the shipped fields.

**Plots.** Only `2006/plots/66/` exists: ~27,474 PNGs across subdirs `anommap`,
`anommapsig`, `avmap(+nomean)`, `avmapsig(+nomean)`, `map`, `mapsig`, `meanmap`,
`meanmapsig`, `seasons`. Generated by `wrapcugnplots_2006.m` → `wrapperanomplots.m`.
**`2017/plots` is empty (0 PNGs); no plots for lines other than 66.**

**Website.** `web/cugn-climatology/new.php` (1232 lines) is the 2026 beta page;
it lists NetCDF downloads and drives interactive figures via
`assets/catalog2026.js`, which loads a daily-generated `assets/file_info2026.json`.

**Not present on this laptop:** the MATLAB `.mat` inputs (`anncycXX.mat`,
`mapXX.mat`) and the Level-3 combined-mission source data — so the pipeline can
be documented but not executed here. Flagged in Q&A.

### 2026-07-17 (Wrote the comprehensive context file)

Checked the user's Q&A answers (comprehensive/detailed doc to guide the Python
port; document as-designed, no MATLAB execution; include website mechanics;
record canonical parameters; 2006=lt / 2017=st confirmed; no st plots exist) and
wrote `context/context_cugn_2026beta.md`.

To write it accurately I read the core MATLAB math (not just the drivers):
- `annualcycleg_var_covm.m` / `anncycinterp.m` — the Gaussian-windowed harmonic
  annual-cycle fit (K=3, ω=2π/365.25 d, xwidth=15 km) and its evaluation; the
  `constant` term is the mean.
- `climatologyCCS_New.m` + `computeCovMtrx.m` + `generateHovMap_AnomOnly.m` —
  the objective analysis (Gauss–Markov) that produces interannual anomalies
  (Lx=30 km, Lt=60 d, noise=0.1, map = B·(A⁻¹d)).
- `allanommap.m`, `anommap2map.m`, `map2anommap.m`, `anncyc2avmap_var.m`,
  `anncyc2meanmap_var.m`, `demeanmap.m`, `interpmap_sigma.m` — how the 10
  products are assembled and the `*tm/*em/*sig` suffixes map to the NetCDFs.
- `addderivedvars.m` — derived vars via **EOS-80 `sw_*`** (theta/rho/sigma/geov/
  ox); important for the Python port.
- `topomask.m` / `errmask.m` / `datemask.m` — the three masks; datemask holds
  per-line start dates (66:2007-04-20, 80:2006-02-26, 90:2006-10-20,
  al:2019-01-01, 56:2019-12-13) that explain the differing record starts.
- Product configs' `data_product` blocks — the exact source-variable mapping
  (e.g. mean_depth←meanmaptm, annual_cycle_depth←avmapnomeantm [mean-removed],
  mean_annual_cycle_depth←avmaptm [full], total_depth←maptmem, anomaly←anommaptmem).
- Website `new.php` (interactive PNG explorer: experiment/baseline/variable/
  plot/dimension/projection/subset controls + Data Access downloads) and
  `catalog2026.js` (loads daily `file_info2026.json`; static PNG+JSON driven).

The context file (12 sections) covers: the two runs, the 10 products + source
map, grids, the full pipeline step-by-step, a canonical-parameters table, the
config schema, NetCDF conventions, plots, website mechanics, explicit guidance
for the Python port, a key-file reference table, and known gotchas (doxy
units mismatch, chl-a missing from mean_sigma, DO st-only, topomask stripes,
rolling-product padding, EOS-80 vs TEOS-10).

Left uncommitted per repo convention.

### 2026-07-17 (Read Rudnick et al. 2017; added §13 to the context file)

Read the reference paper `context/rudnick2017.pdf` (Rudnick, Zaba, Todd & Davis
2017, *Prog. Oceanogr.* 154, 64–106) and added a new **§13** to
`context/context_cugn_2026beta.md` summarizing it, plus a header row and a
refined baseline note.

What the paper adds/confirms:
- **It is the methodology paper of record.** The 2026 beta is its operational
  continuation: the paper covers the `lt` foundation (3 lines 66.7/80/90, T/S/
  velocity only, base years 2007–2013); the 2026 beta extends it with lines
  56.7 + alongshore, chlorophyll/backscatter/**oxygen**, the `st` run, and
  rolling updates. The paper even flags Doppler/fluorescence as "may be added in
  future" — now realized.
- **Authoritative method parameters**, matching the MATLAB I read: annual cycle =
  constant + 3 harmonics (7 functions), period 365.25 d, 5 km spacing, Gaussian
  along-line window **L = 15 km** (from the T spectrum break at k₀=0.03 cpkm);
  anomaly objective map with **time scale 60 d, length scale 30 km**,
  noise/signal 0.1, on 10 m × 5 km × 10 d, masked where error/signal > 0.3.
- **Base-year clarification (corrects my earlier note):** the annual cycle is
  fit over complete years **2007–2013 (90/80), 2008–2013 (66.7)**, deliberately
  stopping before 2014 to keep the 2014–2016 warm anomaly out of the base cycle
  — consistent with the `lt` mean `time_coverage` attr (2007-01-01→2014-01-01).
- **Mean geostrophic velocity is referenced to the glider depth-average
  (absolute) velocity** via thermal wind — a distinguishing capability.
- **SoCal Temperature Index** (Line 90, 50 m, 0–200 km, 3-mo running mean) tracks
  the Oceanic Niño Index — a ready validation target for the Python port. The
  paper's Blob (2014–2016) discussion matches the interannual signal our own §8c
  analysis recovered.
- **Distribution** described in the paper (menu-driven figures + CF NetCDF at
  spraydata.ucsd.edu) matches the website layer documented in §9.

Read the paper in three PDF passes (intro/methods/mean, annual-cycle results,
interannual + conclusions/references). Context file left uncommitted.