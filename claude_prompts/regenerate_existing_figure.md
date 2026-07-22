# Text to existing figure

This prompt doc will try to grab existing PNG figures that Dan provided by using text prompts only.

## Context 

- There are a set of JSON config files at `$OS_SPRAY/CUGN/Climatology/Original/config/` that were used to generate the `2026 beta` climatology.
- There is a large set of PNG figures in `$OS_SPRAY/CUGN/Climatology/Original/2006/plots/66/` that are currently used for the website.
- The file `$OS_SPRAY/CUGN/Climatology/Original/web/cugn-climatology/new.php` is the source for the `2026 beta` climatology website.
- The folder `$OS_SPRAY/CUGN/Climatology/Original/src_231/` contains the MATLAB code that was used to generate the `2026 beta` climatology.

Also be reminded of these two files in `context/` that you have generated:

- `context/context_cugn_2026beta.md`
- `context/initial_exploration.md`

## Prompts

1. We are going to ask you to identify a specific PNG figure by only providing you a text description of the figure.  Before we do so, do you have any questions about this?  If so, add to the Q&A section below.  Log your work in the Logs section.  Use Fable if you can.

2. I have answered the questions in the Q&A section; please check my answers.  If you have any new questions, please add to the Q&A section below.  Log your work in the Logs section.  Use Fable if you can.

3. Ok, we are ready now.  Here is your first assignment:

Please give me the plot of the internannual anomaly of the temperature at 50m depth.  

If you can't find any such plot, report so and provide your reasoning.  Use Fable if you can. Log your work in the Logs section.

4. Ok, that's great.  Here is your second assignment:

Please give me the plot of potential density on Line 66 on January 11, 2026.  

If you can't find any such plot, report so and provide your reasoning.  Use Fable if you can. Log your work in the Logs section.

## Q&A

I decoded the figure-naming grammar (see Logs). Filenames follow
`<line>_<product>_<axis>_<var>[_<slice>].png` — e.g.
`66_map_xz_t_2008-03-31.png` (total temperature section on 2008-03-31),
`66_mapsig_xtime_abs_26.8.png` (backscatter Hovmöller on the σ=26.8 surface).
Before you give me a description, a few questions so I return the right file:

**1. Target set — line 66 / long-term only?** The only PNGs present are
`2006/plots/66/` (the `lt` run, **line 66**, ~27,500 files). Will every
description resolve to a figure in this set, or might one reference a line
(56/80/90/along) or the `st` run for which **no PNGs exist here**? If the latter,
the honest answer will be "no matching file present."
>A. Yes, only line 66 is present.

**2. What should I return, and how many?** A single exact file path (the best
match), or a short ranked list when the description is ambiguous? And should I
give the absolute path under `$OS_SPRAY/.../2006/plots/66/…`?
>A. To start with, one file.  The full path please.

**3. Will descriptions use science language or filename tokens?** I plan to map
natural descriptions to tokens — e.g. "potential density" → `sigma`,
"cross-shore section" → `xz`, "Hovmöller / distance–time" → `xtime`,
"time–depth at a fixed distance" → `timez`, "mean" → `meanmap`, "annual cycle"
→ `avmap` (full) vs "annual anomaly / mean-removed" → `avmapnomean`,
"interannual anomaly" → `anommap`, "total" → `map`. Confirm you'll describe the
science (not hand me the raw tokens), and that this mapping matches your intent —
especially the annual-cycle (`avmap`) vs annual-anomaly (`avmapnomean`)
distinction.
>A. Science language please.

**4. How exact will the slice be?** Time-varying sections carry a specific value
in the name — a **date** (e.g. `map_xz_t` has 711 distinct dates), a **depth**
(`xtime`/`timez`, in m), a **distance** (`timez`, km), or a **σ-surface**
(sig products). If you specify the exact value I can pin the file; if you give a
qualitative one ("a warm section during the 2015 El Niño"), I'd return the
nearest candidate(s) — is nearest-match acceptable, or will you always give an
exact slice?
>A. Nearest-match is desired.  The language used may be imprecise.  Please provide an estimate of your certainty in the answer.

**5. May I open candidate PNGs to visually confirm?** I can view the images to
verify a match (e.g. confirm a section really shows the described feature). Do
you want me to (a) identify by filename reasoning only, or (b) also open the
top candidate(s) and confirm visually before answering? Visual confirmation is
slower but safer for ambiguous descriptions.
>A. Yes you may.

---

Answers received and understood. Confirmed I can open Dan's PNGs — they carry
titles (e.g. "Line 66.7, Mean"), axis labels, colorbar labels, and density
contours, so visual confirmation is reliable. Two small follow-ups:

**6 (new). "Seasonal" sections — composite vs a dated section?** A description
like "summer temperature cross-section" is genuinely ambiguous between:
(a) the **seasonal composite** in `seasons/` (`66_xz_t_summer.png` — a
JJA-averaged section), and (b) a single **dated total section** that happens to
fall in summer (`map/66_xz_t_<YYYY-MM-DD>.png`). Unless you indicate a specific
year/date (→ dated section) or say "climatological/typical/composite"
(→ seasons), my default will be the **seasonal composite**. OK? (I'll state which
I chose and my certainty.)
>A. If we say summer, default to the seasonal composite.  If we say season, grab the corresponding seasonal composite.

**7 (new). Certainty format.** I'll report certainty as a **percentage plus one
line of reasoning** (e.g. "≈85% — product/variable/axis unambiguous; slice
picked as nearest of 711 dates"), and note the main alternative if it's close.
Works for you?
>A. Sure.  

## Logging

Append an entry to the **Logs** section of this file using the format:

```
### <Date> (Short summary of the work)

<Detailed description of the work and what you learned>
```

## Logs

### 2026-07-17 (Decoded the figure-naming grammar; asked questions)

Before the text→figure retrieval task, I reverse-engineered the naming scheme of
the ~27,500 PNGs in `$OS_SPRAY/CUGN/Climatology/Original/2006/plots/66/` (the
only plots present: `lt` run, line 66) and posted clarifying questions in Q&A.

**Grammar:** `<line>_<product>_<axis>_<var>[_<slice>].png`

- **line:** always `66` here.
- **product** (= subdirectory): `mean`/`meanmapsig` (time mean); `avmap`/`avmapsig`
  (full **annual cycle** = mean_annual_cycle); `avmapnomean`/`avmapsignomean`
  (**annual anomaly**, mean removed); `map`/`mapsig` (**total**); `anommap`/
  `anommapsig` (**interannual anomaly**); `seasons` (seasonal composites, token
  order `66_xz_<var>_<season>`). The `*sig` variants are on potential-density
  surfaces; the rest are on depth.
- **axis:** `xz` = cross-shore distance × depth section; `xtime` = Hovmöller
  (distance × time) at a fixed level; `timez` = time × depth at a fixed distance;
  `time` = time series at a fixed (depth/σ, distance).
- **var:** `t, s, fl, rho, sigma, theta, geov, abs, udopalong, udopacross,
  oxumolkg, depth` (matvarnames from `variables.json`; `depth` appears on sig
  products as isopycnal depth).
- **slice** encodes the fixed value: a **date** `YYYY-MM-DD` for time-varying
  sections (`map`/`anommap` `xz` — 711 distinct dates for `map_xz_t`), a **depth
  in m** or **σ value** for `xtime`, a **distance in km** for `timez`, `<depth/σ>_<dist>`
  for `time`, a two-number day token for `avmap` `xz`, and a **season**
  (winter/spring/summer/fall) for `seasons`.

**Subdir counts (line 66):** anommap 7657, anommapsig 5860, map 6057, mapsig
5229, avmap 821, avmapnomean 821, avmapsig 488, avmapsignomean 488, seasons 36,
meanmap 9, meanmapsig 8.

**Questions raised** (Q&A): target set (line 66 / lt only — no PNGs for other
lines or `st`); single vs ranked output; science language vs raw tokens (and
confirming the annual-cycle `avmap` vs annual-anomaly `avmapnomean` mapping);
how exact the slice value will be (exact vs nearest-match); and whether I may
open candidate PNGs to confirm visually. Awaiting answers before the first
retrieval.

### 2026-07-17 (Reviewed answers; confirmed readiness; two follow-ups)

Checked the user's Q&A answers and confirmed my retrieval approach:
- **Scope:** line 66 only (long-term run) — anything else → "no matching file."
- **Output:** a single best match, full absolute path.
- **Input:** science language; I map it to tokens (product/axis/variable/slice).
- **Ambiguity:** nearest-match is acceptable and language may be imprecise;
  I must report a **certainty estimate**.
- **Verification:** I may open candidate PNGs to confirm visually.

Verified I can open Dan's PNGs (viewed `meanmap/66_mean_xz_t.png`): they include
a **title** ("Line 66.7, Mean"), axis labels ("Offshore Distance (km)",
"Depth (m)"), a labeled colorbar, and σ contours — so visual confirmation is
reliable, and titles should reveal the date/season for time-varying figures.

Raised two small follow-ups in Q&A: (6) how to treat "seasonal" descriptions —
default to the `seasons/` composite unless a specific date/year is given; and
(7) certainty reported as a percentage + one line of reasoning. Ready to receive
the first figure description.

### 2026-07-17 (Retrieval #1: interannual T anomaly at 50 m — matched)

**Request:** "the interannual anomaly of the temperature at 50 m depth."

**Answer (full path):**
`/home/xavier/Projects/Oceanography/data/Spray/CUGN/Climatology/Original/2006/plots/66/anommap/xtime/t/66_anommap_xtime_t_50.png`

**Certainty: ≈95%.** Reasoning: "interannual anomaly" → `anommap`;
"temperature" → `t`; "at 50 m depth" fixes depth → the `xtime` Hovmöller
(offshore distance × time at a fixed depth), slice = 50 m — an exact available
depth (10–500 m by 10 m), no nearest-match needed. Verified visually: title
"Line 66.7, 50 m", colorbar "Anomaly of Temperature (°C)", x = Offshore Distance
(km), y = time 2007→2025+ (shows the 2014–2016 warm bands, 2011 cold band, and
2025–26 warm event). The only interpretive choice was axis type: "at 50 m"
fixes depth → `xtime`, as opposed to `timez` (time×depth at a fixed *distance*)
or a dated `xz` section; hence ~95%, not 100%.

**Correction to the grammar (Logs, 2026-07-17):** the plots are **nested** by
axis/variable — the file lives at `anommap/xtime/t/`, not flat in `anommap/`.
Full layout is `.../66/<product>/<axis>/<var>/<line>_<product>_<axis>_<var>[_<slice>].png`.
(My earlier `find -type f` recursed so counts/patterns were right, but paths
must include the `<axis>/<var>/` subdirs.)

### 2026-07-17 (Retrieval #2: potential density on Jan 11, 2026 — no exact match)

**Request:** "potential density on Line 66 on January 11, 2026."

**Answer: no such plot exists.** Potential density (`sigma`) is **not** rendered
as a standalone colored field in any *time-varying* product — under `map/`
(total) and `anommap/` (interannual anomaly) the plotted `xz`/`xtime`/`timez`
variables are only `t, s, fl, theta, geov, abs, udopalong, udopacross` (no
`sigma` subdirectory in either). So there is no date-specific
(2026-01-11) potential-density figure. **Certainty ≈97%** that no exact match
exists — verified by enumerating every variable subdir under `map/` and
`anommap/` and finding no `sigma`/`rho`, and by confirming the date itself does
render (see below).

Where potential density *does* appear:
- As a **standalone colored field only in time-independent products**:
  `meanmap/66_mean_xz_sigma.png` (mean), the seasonal composites
  `seasons/66_xz_sigma_{winter,spring,summer,fall}.png`, and the annual-cycle
  products (`avmap`/`avmapnomean` on xz/xtime/timez).
- As **contour overlays** (σθ = 25, 26, …) on every dated section. Confirmed by
  opening `map/xz/t/66_map_xz_t_2026-01-11.png` — title "Line 66.7, 2026/01/11",
  a temperature field with labeled potential-density contours. The date exists
  (10-day cadence: 2026-01-01, -11, -21, -31; record runs to 2026-07-10).

Nearest alternatives offered to the user:
1. For potential density *on that date*: the dated section carrying σ contours,
   `.../map/xz/t/66_map_xz_t_2026-01-11.png` (density as contours, T as color).
2. For a standalone potential-density section (not date-specific): the mean
   `.../meanmap/66_mean_xz_sigma.png`, or the winter composite
   `.../seasons/66_xz_sigma_winter.png` (January → winter).

Root cause: in the generating code, σθ is a derived/overlay field on the
time-varying maps, plotted as its own color field only for the mean/seasonal/
annual-cycle products — consistent with the MATLAB plotting wrappers.
