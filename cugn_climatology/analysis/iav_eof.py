"""iav_eof: leading EOF modes of the lt Line 90 temperature-anomaly field.

Domain: 0-300 m depth x full cross-shore section. Grid points valid at every
retained (trimmed) time step are used; the anomaly is already mean/seasonal-
removed so no further detrending. SVD-based EOF, no area weighting beyond the
native grid (uniform 10 m x 5 km cells).

Fig iav_eof.png: EOF1/EOF2 spatial patterns (depth x distance) and their PCs.
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
da3 = da.sel(depth=depth[zsel])            # (time, depth, distance)
nz = zsel.sum()
nx = dist.size
X = da3.values.reshape(da3.shape[0], nz * nx)   # (ntime, npts)

# keep grid points finite at ALL times
good = np.all(np.isfinite(X), axis=0)
print(f"grid pts total {X.shape[1]}, retained {good.sum()}")
Xg = X[:, good]
Xm = Xg - Xg.mean(axis=0, keepdims=True)   # anomaly of anomaly (~0 mean)

U, S, Vt = np.linalg.svd(Xm, full_matrices=False)
var = S**2 / np.sum(S**2)
print("variance explained EOF1-4:", np.round(var[:4] * 100, 1))

# reconstruct spatial maps on full grid
def spatial_map(k):
    full = np.full(nz * nx, np.nan)
    full[good] = Vt[k]
    return full.reshape(nz, nx)

pcs = U * S  # (ntime, modes); PC amplitudes

fig, axes = plt.subplots(2, 2, figsize=(13, 8))
for k in range(2):
    emap = spatial_map(k)
    # sign convention: positive surface loading
    surf_load = np.nanmean(emap[:5, :])
    sgn = np.sign(surf_load) if surf_load != 0 else 1
    emap *= sgn
    pc = pcs[:, k] * sgn
    ax = axes[0, k]
    vmax = np.nanmax(np.abs(emap))
    im = ax.pcolormesh(dist, depth[zsel], emap, cmap=cmocean.cm.balance,
                       vmin=-vmax, vmax=vmax, shading="nearest")
    ax.invert_yaxis()
    ax.set_title(f"EOF{k+1} ({var[k]*100:.1f}% var)")
    ax.set_xlabel("cross-shore (km)")
    ax.set_ylabel("depth (m)")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    axp = axes[1, k]
    axp.plot(t, pc, color="0.2", lw=1.2)
    axp.axhline(0, color="k", lw=0.6)
    axp.set_title(f"PC{k+1}")
    axp.set_xlabel("year")
fig.suptitle(f"CUGN lt Line {LINE} T-anomaly EOFs (0-300 m)", y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.96])
out = f"{FIGDIR}/iav_eof.png"
fig.savefig(out)
print("wrote", out)

# correlate PC1 with surface cross-shore-mean anomaly for interpretation
surf = da3.sel(depth=10.).mean(dim="distance", skipna=True).values
pc1 = pcs[:, 0]
pc1 *= np.sign(np.corrcoef(pc1, surf)[0, 1])
print("corr(PC1, 10m cross-shore-mean anom) =",
      round(np.corrcoef(pc1, surf)[0, 1], 2))
