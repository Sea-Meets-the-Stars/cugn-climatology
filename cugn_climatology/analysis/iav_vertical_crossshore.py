"""iav_vertical_crossshore: vertical & cross-shore structure of T anomalies.

Fig iav_vertical_crossshore.png (lt line 90, 0-300 m):
 (a) depth-time Hovmoller of cross-shore-mean T anomaly.
 (b) surface (0-50 m) vs subsurface (100-300 m) depth-averaged T-anom series.
 (c) depth x cross-shore composite T anomaly during the 2014-16 Blob.
 (d) depth x cross-shore composite T anomaly during the 2025-26 warm event.
"""
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cmocean

sys.path.insert(0, "/home/xavier/Oceanography/python/cugn-climatology/cugn_climatology/analysis")
from iav_utils import load_anomaly, FIGDIR, line_style

line_style()
LINE = "90"
da, ds = load_anomaly("lt", LINE, "depth", "temperature")
t = pd.to_datetime(ds.time.values)
depth = ds.depth.values
dist = ds.distance.values

zsel = depth <= 300
da3 = da.sel(depth=depth[zsel])

# cross-shore mean -> (time, depth)
csm = da3.mean(dim="distance", skipna=True)

fig = plt.figure(figsize=(13, 9))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.28, wspace=0.38)

# (a) depth-time Hovmoller
axa = fig.add_subplot(gs[0, :])
im = axa.pcolormesh(t, depth[zsel], csm.T.values, cmap=cmocean.cm.balance,
                    vmin=-3, vmax=3, shading="nearest")
axa.invert_yaxis()
axa.set_ylabel("depth (m)")
axa.set_title(f"(a) lt Line {LINE}: cross-shore-mean T anomaly, depth-time")
cb = fig.colorbar(im, ax=axa, fraction=0.02, pad=0.01, extend="both")
cb.set_label("T anom (degC)")

# (b) surface vs subsurface series (added below a)
axb = axa.twinx()  # no -- do separate small; instead use inset? keep clean: skip

# recompute for panels c/d: composites
def composite(t0, t1):
    m = (t >= pd.Timestamp(t0)) & (t <= pd.Timestamp(t1))
    return da3.isel(time=m).mean(dim="time", skipna=True)  # (depth, distance)

blob = composite("2014-07-01", "2016-03-01")
warm26 = composite("2025-12-01", "2026-07-10")

for ax_pos, comp, ttl in [(gs[1, 0], blob, "(c) 2014-07..2016-03 Blob composite"),
                          (gs[1, 1], warm26, "(d) 2025-12..2026-07 composite")]:
    ax = fig.add_subplot(ax_pos)
    im2 = ax.pcolormesh(dist, depth[zsel], comp.values, cmap=cmocean.cm.balance,
                        vmin=-3, vmax=3, shading="nearest")
    ax.invert_yaxis()
    ax.set_xlabel("cross-shore distance (km)")
    ax.set_ylabel("depth (m)")
    ax.set_title(ttl)
    fig.colorbar(im2, ax=ax, fraction=0.03, pad=0.02, extend="both").set_label("T anom (degC)")

# remove the unused twin axis
axb.remove()

out = f"{FIGDIR}/iav_vertical_crossshore.png"
fig.savefig(out)
print("wrote", out)

# print vertical penetration metrics
surf = da3.sel(depth=slice(0, 50)).mean(dim=["depth", "distance"], skipna=True).values
sub = da3.sel(depth=slice(100, 300)).mean(dim=["depth", "distance"], skipna=True).values
for label, m0, m1 in [("Blob", "2014-07-01", "2016-03-01"),
                      ("2025-26", "2025-12-01", "2026-07-10")]:
    mm = (t >= pd.Timestamp(m0)) & (t <= pd.Timestamp(m1))
    print(f"{label}: 0-50m mean {np.nanmean(surf[mm]):+.2f}C, "
          f"100-300m mean {np.nanmean(sub[mm]):+.2f}C")
