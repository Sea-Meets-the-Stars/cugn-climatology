# Context for the CUGN Climatology project

This prompt doc will build the context for the CUGN Climatology project.
We will examine data, code, and config files that were used to generate the `2026 beta` climatology.  We will then generate a context file describing the data, code, and config files called `context/context_cugn_2026beta.md`.

## Process

If you need to run Python, use the "ocean14" conda environment.

## Data

- There are a set of JSON config files at `$OS_SPRAY/CUGN/Climatology/Original/config/` that were used to generate the `2026 beta` climatology.
- There is a large set of PNG figures in `$OS_SPRAY/CUGN/Climatology/Original/2006/plots/66/` that are currently used for the website.
- The file `$OS_SPRAY/CUGN/Climatology/Original/web/cugn-climatology/new.php` is the source for the `2026 beta` climatology website.
- The folder `$OS_SPRAY/CUGN/Climatology/Original/src_231/` contains the MATLAB code that was used to generate the `2026 beta` climatology.

## Prompts

1, Examine the data, code, and config files described in the `Data` section above.  Ask me a set of questions in the Q&A section below before writing the context file.  Log your work in the Logs section.  Use Fable if you can.

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