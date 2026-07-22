"""Quantitative BGC diagnostics across CUGN st lines."""
import numpy as np
from bgc_common import open_ds, HYPOXIC, SEVERE

LINES = ['56', '66', '80', '90', 'al']

print("=== Mean OMZ / hypoxia diagnostics (st mean depth) ===")
for line in LINES:
    ds = open_ds('st', 'mean', 'depth', line)
    doxy = ds['doxy']              # (depth, distance)
    depth = ds['depth'].values
    dist = ds['distance'].values
    vals = doxy.values
    # OMZ: absolute minimum
    imin = np.unravel_index(np.nanargmin(vals), vals.shape)
    omz_val = vals[imin]
    omz_depth = depth[imin[0]]
    omz_dist = dist[imin[1]]
    # depth of minimum per column (upper 500m already)
    # shallowest hypoxic depth (outcrop) per column
    outcrops = []
    for j in range(vals.shape[1]):
        col = vals[:, j]
        hyp = np.where(col < HYPOXIC)[0]
        if len(hyp) > 0:
            outcrops.append(depth[hyp[0]])
    outcrops = np.array(outcrops)
    shallowest_hyp = outcrops.min() if len(outcrops) else np.nan
    # fraction of valid grid that is hypoxic
    valid = ~np.isnan(vals)
    frac_hyp = np.nansum(vals < HYPOXIC) / valid.sum()
    frac_sev = np.nansum(vals < SEVERE) / valid.sum()
    # doxy at 10 m offshore (surface saturation)
    surf = np.nanmedian(vals[0, :])
    print(f"Line {line:>2}: OMZ_min={omz_val:6.1f} umol/kg at z={omz_depth:.0f}m, "
          f"dist={omz_dist:.0f}km | shallowest hypoxic z={shallowest_hyp:.0f}m | "
          f"hypoxic frac={frac_hyp:.2f} severe={frac_sev:.3f} | surf(10m)~{surf:.0f}")
    ds.close()

print("\n=== SCM vs O2 (Line 90, upper 150 m) ===")
ds = open_ds('st', 'mean', 'depth', '90')
depth = ds['depth'].values
dist = ds['distance'].values
chl = ds['chlorophyll_a'].values
doxy = ds['doxy'].values
u = depth <= 150
for jlab, j in [('inshore ~50km', np.argmin(np.abs(dist-50))),
                ('mid ~200km', np.argmin(np.abs(dist-200))),
                ('offshore ~400km', np.argmin(np.abs(dist-400)))]:
    ccol = chl[u, j]
    if np.all(np.isnan(ccol)):
        continue
    kmax = np.nanargmax(ccol)
    scm_z = depth[u][kmax]
    o2_at_scm = doxy[u, j][kmax]
    print(f"{jlab}: SCM z={scm_z:.0f}m chl={ccol[kmax]:.2f} mg/m3, O2 there={o2_at_scm:.0f} umol/kg")
ds.close()

print("\n=== Interannual doxy trend (Line 90, total) ===")
from bgc_common import trim_trailing_nan
ds = trim_trailing_nan(open_ds('st', 'total', 'depth', '90'))
t = ds['time'].values.astype('datetime64[D]').astype(float) / 365.25  # years
depth = ds['depth'].values
dist = ds['distance'].values
doxy = ds['doxy'].values  # (time, depth, distance)
# distance-averaged then trend per depth
prof = np.nanmean(doxy, axis=2)  # (time, depth)
yrs = t - t[0]
print(f"record: {ds['time'].values[0]} -> {ds['time'].values[-1]}, n={len(t)}")
for zt in [50, 100, 150, 200, 300]:
    k = np.argmin(np.abs(depth - zt))
    y = prof[:, k]
    m = np.isfinite(y)
    if m.sum() < 10:
        continue
    slope, b = np.polyfit(yrs[m], y[m], 1)
    print(f"  z={zt:>3}m: doxy trend = {slope:+.2f} umol/kg/yr (mean {np.nanmean(y):.0f})")
ds.close()

print("\n=== Backscatter vertical structure (Line 90 mean) ===")
ds = open_ds('st', 'mean', 'depth', '90')
depth = ds['depth'].values
bs = ds['acoustic_backscatter'].values
prof = np.nanmedian(bs, axis=1)
for k in range(0, len(depth), 5):
    print(f"  z={depth[k]:>3.0f}m: backscatter={prof[k]:.1f} dB")
ds.close()
