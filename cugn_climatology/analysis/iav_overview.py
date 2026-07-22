"""iav_overview: interannual 10 m temperature-anomaly Hovmoller diagrams.

Fig iav_hovmoller_lt.png : lt group (2006-2026 record, 2007-2014 baseline),
  lines 66/80/90 -- time x cross-shore distance, 10 m T anomaly.
Also prints the warmest / coolest events and their timing.
"""
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cmocean

sys.path.insert(0, "/home/xavier/Oceanography/python/cugn-climatology/cugn_climatology/analysis")
from iav_utils import load_anomaly, FIGDIR, line_style

line_style()

LINES = ["66", "80", "90"]
Z = 10.0  # surface level

fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
for ax, line in zip(axes, LINES):
    da, ds = load_anomaly("lt", line, "depth", "temperature")
    surf = da.sel(depth=Z)            # (time, distance)
    t = pd.to_datetime(ds.time.values)
    dist = ds.distance.values
    im = ax.pcolormesh(t, dist, surf.T.values, cmap=cmocean.cm.balance,
                       vmin=-3, vmax=3, shading="nearest")
    ax.set_ylabel(f"Line {line}\ncross-shore (km)")
    ax.set_ylim(dist.max(), 0)  # inshore at bottom
    # annotate record-mean cross-shore-averaged series stats
    ser = surf.mean(dim="distance", skipna=True)
    imax = int(np.nanargmax(ser.values))
    imin = int(np.nanargmin(ser.values))
    print(f"[lt line {line}] 10m T anomaly (cross-shore mean): "
          f"max {ser.values[imax]:+.2f}C @ {t[imax].date()}, "
          f"min {ser.values[imin]:+.2f}C @ {t[imin].date()}, "
          f"record {t[0].date()}..{t[-1].date()}")

axes[0].set_title("CUGN lt interannual anomaly, 10 m temperature (2007-2014 baseline)")
axes[-1].set_xlabel("year")
cb = fig.colorbar(im, ax=axes, orientation="vertical", fraction=0.02, pad=0.02,
                  extend="both")
cb.set_label("T anomaly (degC)")
out = f"{FIGDIR}/iav_hovmoller_lt.png"
fig.savefig(out)
print("wrote", out)
