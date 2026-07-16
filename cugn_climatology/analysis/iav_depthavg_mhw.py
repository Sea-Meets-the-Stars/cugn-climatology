"""iav_depthavg_mhw: depth-averaged (0-100 m) anomaly time series per line and
a simple marine-heatwave / cold-spell index.

Metrics (cross-shore mean, lt group):
 - 0-100 m depth-averaged T anomaly time series, all lines.
 - surface (10 m) T-anomaly MHW index: flag steps above the 90th-percentile
   anomaly threshold (Hobday-style, but seasonal cycle already removed).
   Cold spells: below the 10th percentile.

Fig iav_depthavg_mhw.png : (a) 0-100 m T anomaly per line; (b) line-90 surface
   T anomaly with MHW/cold thresholds and shaded events; (c) line-90 salinity
   and chlorophyll 0-100 m anomalies.
"""
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, "/home/xavier/Oceanography/python/cugn-climatology/cugn_climatology/analysis")
from iav_utils import load_anomaly, depth_average, FIGDIR, line_style

line_style()
LINES = ["66", "80", "90"]
COL = {"66": "#1b9e77", "80": "#d95f02", "90": "#7570b3"}


def csmean_depthavg(group, line, var, zmax=100.):
    da, ds = load_anomaly(group, line, "depth", var)
    davg = depth_average(da, zmax)                 # (time, distance)
    ser = davg.mean(dim="distance", skipna=True)   # (time,)
    return pd.to_datetime(ds.time.values), ser.values


fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

# (a) 0-100 m T anomaly, all lines
axa = axes[0]
for line in LINES:
    t, y = csmean_depthavg("lt", line, "temperature")
    axa.plot(t, y, color=COL[line], lw=1.3, label=f"Line {line}")
axa.axhline(0, color="k", lw=0.6)
axa.set_ylabel("0-100 m T anom (degC)")
axa.set_title("CUGN lt 0-100 m depth-averaged, cross-shore-mean temperature anomaly")
axa.legend(ncol=3, fontsize=9)

# (b) MHW index on 10 m surface anomaly, line 90
axb = axes[1]
da, ds = load_anomaly("lt", "90", "depth", "temperature")
surf = da.sel(depth=10.).mean(dim="distance", skipna=True)
t = pd.to_datetime(ds.time.values)
y = surf.values
hi = np.nanpercentile(y, 90)
lo = np.nanpercentile(y, 10)
axb.plot(t, y, color="0.2", lw=1.2)
axb.axhline(0, color="k", lw=0.6)
axb.axhline(hi, color="firebrick", ls="--", lw=1, label=f"90th pct (+{hi:.2f})")
axb.axhline(lo, color="navy", ls="--", lw=1, label=f"10th pct ({lo:.2f})")
axb.fill_between(t, hi, y, where=(y > hi), color="firebrick", alpha=0.6, interpolate=True)
axb.fill_between(t, lo, y, where=(y < lo), color="navy", alpha=0.5, interpolate=True)
axb.set_ylabel("10 m T anom (degC)")
axb.set_title("Line 90 surface (10 m) T anomaly: MHW (red) / cold-spell (blue) index")
axb.legend(fontsize=9, loc="upper left")

# MHW event stats: contiguous runs above threshold
def runs(mask, t, y):
    out = []
    i = 0
    n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            seg = slice(i, j)
            dur_days = (t[j-1] - t[i]).days + 10
            out.append((t[i].date(), t[j-1].date(), dur_days,
                        float(np.nanmax(np.abs(y[seg])))))
            i = j
        else:
            i += 1
    return out

valid = ~np.isnan(y)
mhw = (y > hi) & valid
cold = (y < lo) & valid
print(f"Line90 surface: MHW threshold={hi:+.2f}C, {mhw.sum()} steps "
      f"({100*mhw.sum()/valid.sum():.1f}% of valid)")
print("MHW events (start,end,dur_days,peak|anom|):")
for e in runs(mhw, t, y):
    if e[2] >= 30:
        print("  ", e)
print("Cold-spell events:")
for e in runs(cold, t, y):
    if e[2] >= 30:
        print("  ", e)

# (c) salinity + chlorophyll 0-100m anomaly, line 90
axc = axes[2]
ts, ys = csmean_depthavg("lt", "90", "salinity")
axc.plot(ts, ys, color="teal", lw=1.2, label="salinity (PSS-78)")
axc.axhline(0, color="k", lw=0.6)
axc.set_ylabel("0-100 m S anom", color="teal")
axc.tick_params(axis="y", labelcolor="teal")
axc2 = axc.twinx()
tc, yc = csmean_depthavg("lt", "90", "chlorophyll_a")
axc2.plot(tc, yc, color="darkgreen", lw=1.0, alpha=0.7, label="chlorophyll")
axc2.set_ylabel("0-100 m chl anom (mg m-3)", color="darkgreen")
axc2.tick_params(axis="y", labelcolor="darkgreen")
axc2.grid(False)
axc.set_title("Line 90 0-100 m salinity and chlorophyll anomalies")
axc.set_xlabel("year")

out = f"{FIGDIR}/iav_depthavg_mhw.png"
fig.savefig(out)
print("wrote", out)
