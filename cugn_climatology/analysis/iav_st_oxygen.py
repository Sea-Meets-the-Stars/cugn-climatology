"""iav_st_oxygen: recent (2017-2026) anomalies incl. dissolved oxygen (st only).

Fig iav_st_oxygen.png (st Line 90, 0-300 m, cross-shore mean):
 (a) T anomaly depth-time Hovmoller.
 (b) dissolved-oxygen anomaly depth-time Hovmoller.
 (c) 0-100 m doxy anomaly time series, st lines 66/80/90.
"""
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cmocean

sys.path.insert(0, "/home/xavier/Oceanography/python/cugn-climatology/cugn_climatology/analysis")
from iav_utils import load_anomaly, depth_average, FIGDIR, line_style

line_style()

fig, axes = plt.subplots(3, 1, figsize=(11, 11))

# (a) T and (b) doxy Hovmoller for st line 90
daT, dsT = load_anomaly("st", "90", "depth", "temperature")
tT = pd.to_datetime(dsT.time.values)
depth = dsT.depth.values
zsel = depth <= 300
csT = daT.sel(depth=depth[zsel]).mean(dim="distance", skipna=True)
im0 = axes[0].pcolormesh(tT, depth[zsel], csT.T.values, cmap=cmocean.cm.balance,
                         vmin=-3, vmax=3, shading="nearest")
axes[0].invert_yaxis()
axes[0].set_ylabel("depth (m)")
axes[0].set_title("(a) st Line 90 cross-shore-mean T anomaly")
fig.colorbar(im0, ax=axes[0], fraction=0.02, pad=0.01, extend="both").set_label("degC")

daO, dsO = load_anomaly("st", "90", "depth", "doxy")
print("doxy units:", daO.attrs.get("units"))
tO = pd.to_datetime(dsO.time.values)
csO = daO.sel(depth=depth[zsel]).mean(dim="distance", skipna=True)
ovmax = np.nanpercentile(np.abs(csO.values), 98)
im1 = axes[1].pcolormesh(tO, depth[zsel], csO.T.values, cmap=cmocean.cm.balance,
                         vmin=-ovmax, vmax=ovmax, shading="nearest")
axes[1].invert_yaxis()
axes[1].set_ylabel("depth (m)")
axes[1].set_title("(b) st Line 90 cross-shore-mean dissolved-oxygen anomaly")
fig.colorbar(im1, ax=axes[1], fraction=0.02, pad=0.01, extend="both").set_label(
    daO.attrs.get("units", "doxy"))

# (c) 0-100 m doxy anomaly series across lines
COL = {"66": "#1b9e77", "80": "#d95f02", "90": "#7570b3"}
for line in ["66", "80", "90"]:
    da, ds = load_anomaly("st", line, "depth", "doxy")
    ser = depth_average(da, 100.).mean(dim="distance", skipna=True)
    axes[2].plot(pd.to_datetime(ds.time.values), ser.values,
                 color=COL[line], lw=1.3, label=f"Line {line}")
axes[2].axhline(0, color="k", lw=0.6)
axes[2].set_ylabel("0-100 m doxy anom")
axes[2].set_title("(c) st 0-100 m dissolved-oxygen anomaly")
axes[2].set_xlabel("year")
axes[2].legend(ncol=3, fontsize=9)

out = f"{FIGDIR}/iav_st_oxygen.png"
fig.savefig(out)
print("wrote", out)

# correlation T vs doxy 0-100m line 90
daT100 = depth_average(daT, 100.).mean(dim="distance", skipna=True).values
daO100 = depth_average(daO, 100.).mean(dim="distance", skipna=True).values
m = np.isfinite(daT100) & np.isfinite(daO100)
print("corr(0-100m T anom, doxy anom) line90 =",
      round(np.corrcoef(daT100[m], daO100[m])[0, 1], 2))
