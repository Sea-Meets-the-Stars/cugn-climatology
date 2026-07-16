import os
import numpy as np
import xarray as xr

DDIR = os.path.join(os.environ['OS_SPRAY'], 'CUGN', 'Climatology', '2026 beta')

def p(f):
    return os.path.join(DDIR, f)

# Inspect mean depth line 90
ds = xr.open_dataset(p('st_mean_depth_90.nc'))
print("=== st_mean_depth_90 ===")
print("coords:", list(ds.coords))
print("depth:", ds['depth'].values[:5], '...', ds['depth'].values[-3:])
print("distance:", ds['distance'].values[:3], '...', ds['distance'].values[-3:])
for v in ['doxy', 'acoustic_backscatter', 'chlorophyll_a']:
    da = ds[v]
    print(f"\n--- {v} ---")
    print("dims:", da.dims, "shape:", da.shape)
    print("attrs:", dict(da.attrs))
    vals = da.values
    print("min/median/max:", np.nanmin(vals), np.nanmedian(vals), np.nanmax(vals))
    print("nan frac:", np.isnan(vals).mean())
ds.close()

# sigma file
ds = xr.open_dataset(p('st_mean_sigma_90.nc'))
print("\n=== st_mean_sigma_90 ===")
print("coords:", list(ds.coords))
print("potential_density:", ds['potential_density'].values)
print("has doxy:", 'doxy' in ds, "has chl:", 'chlorophyll_a' in ds)
print("doxy attrs:", dict(ds['doxy'].attrs))
ds.close()

# anomaly time axis check
ds = xr.open_dataset(p('st_anomaly_depth_90.nc'))
print("\n=== st_anomaly_depth_90 time ===")
t = ds['time'].values
print("n_time:", len(t), "first:", t[0], "last:", t[-1])
# find trailing all-nan
doxy = ds['doxy']
# mean over depth,distance
allnan = np.isnan(doxy.values).all(axis=(1,2))
print("num all-nan steps:", allnan.sum())
valid = np.where(~allnan)[0]
print("last valid idx:", valid[-1], "time:", t[valid[-1]])
ds.close()
