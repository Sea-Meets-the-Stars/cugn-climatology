""" Initial exploration of the 2026 beta CUGN climatology files.

Scans every NetCDF file in $OS_SPRAY/CUGN/Climatology/2026 beta and writes
an inventory table to context/file_inventory.csv, plus prints targeted
diagnostics (time coverage, grids, variable ranges, NaN fractions, and a
consistency check that total = mean + annual_cycle + anomaly).

Usage:
    python -m cugn_climatology.explore_2026beta
"""

import os
import glob

import numpy as np
import pandas as pd
import xarray as xr

DATA_DIR = os.path.join(os.environ['OS_SPRAY'], 'CUGN', 'Climatology', '2026 beta')
CONTEXT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'context')


def parse_name(fname: str) -> dict:
    """ Split e.g. lt_mean_annual_cycle_depth_66.nc into its pieces. """
    stem = os.path.basename(fname).replace('.nc', '')
    group, rest = stem.split('_', 1)  # lt / st
    for vc in ['depth', 'sigma']:
        if f'_{vc}_' in rest:
            product, line = rest.split(f'_{vc}_')
            return dict(group=group, product=product, vcoord=vc, line=line)
    raise ValueError(f'Cannot parse {fname}')


def inventory() -> pd.DataFrame:
    """ One row per file: naming pieces, dims, variables, time coverage. """
    rows = []
    for fname in sorted(glob.glob(os.path.join(DATA_DIR, '*.nc'))):
        ds = xr.open_dataset(fname)
        row = parse_name(fname)
        row['file'] = os.path.basename(fname)
        row['dims'] = '; '.join(f'{k}={v}' for k, v in ds.sizes.items())
        row['n_vars'] = len(ds.data_vars)
        row['vars'] = '; '.join(ds.data_vars)
        if 'time' in ds.coords:
            row['time_start'] = str(ds.time.values[0])[:10]
            row['time_end'] = str(ds.time.values[-1])[:10]
            row['n_time'] = ds.sizes.get('time', 0)
        row['title'] = ds.attrs.get('title', '')
        row['time_coverage'] = (ds.attrs.get('time_coverage_start', '') + ' to '
                                + ds.attrs.get('time_coverage_end', ''))
        rows.append(row)
        ds.close()
    return pd.DataFrame(rows)


def targeted_checks():
    """ Grids, ranges, NaN fractions, and the total = mean + cycle + anomaly check. """
    print('\n================ TARGETED CHECKS ================\n')

    # -- Grids for one line, both vertical coordinates
    for f in ['lt_mean_depth_90.nc', 'lt_mean_sigma_90.nc',
              'st_mean_depth_90.nc', 'st_mean_depth_al.nc']:
        path = os.path.join(DATA_DIR, f)
        if not os.path.exists(path):
            continue
        ds = xr.open_dataset(path)
        print(f'== {f}')
        for c in ds.coords:
            vals = ds[c].values
            if vals.ndim == 1 and len(vals) > 1:
                print(f'   {c}: {len(vals)} pts, {vals.min():.2f} to {vals.max():.2f}, '
                      f'step~{np.median(np.diff(vals.astype(float))):.2f}')
        ds.close()

    # -- Variable ranges and NaN fractions (lt mean, line 90, depth)
    ds = xr.open_dataset(os.path.join(DATA_DIR, 'lt_mean_depth_90.nc'))
    print('\n== Variable ranges / NaN fraction: lt_mean_depth_90.nc')
    for v in ds.data_vars:
        arr = ds[v].values
        nan_frac = np.isnan(arr).mean()
        print(f'   {v:32s} min={np.nanmin(arr):9.3f} max={np.nanmax(arr):9.3f} '
              f'NaN={nan_frac:5.1%}  units={ds[v].attrs.get("units", "?")}')
    ds.close()

    # -- Does total = mean + annual_cycle + anomaly? (lt, line 90, depth)
    print('\n== Consistency: total vs mean + annual_cycle + anomaly (lt, depth, line 90)')
    mean = xr.open_dataset(os.path.join(DATA_DIR, 'lt_mean_depth_90.nc'))
    cyc = xr.open_dataset(os.path.join(DATA_DIR, 'lt_annual_cycle_depth_90.nc'))
    anom = xr.open_dataset(os.path.join(DATA_DIR, 'lt_anomaly_depth_90.nc'))
    tot = xr.open_dataset(os.path.join(DATA_DIR, 'lt_total_depth_90.nc'))
    v = 'temperature'
    # Map each anomaly time to a day-of-year index in the 365-day cycle
    doy = tot.time.dt.dayofyear.values.clip(max=365) - 1
    recon = (mean[v].values[None, ...] + cyc[v].values[doy, ...] + anom[v].values)
    diff = np.abs(recon - tot[v].values)
    print(f'   {v}: max |total - (mean+cycle+anomaly)| = {np.nanmax(diff):.4g}')
    print(f'   anomaly time: {str(anom.time.values[0])[:10]} to '
          f'{str(anom.time.values[-1])[:10]}, n={anom.sizes["time"]}, '
          f'step~{np.median(np.diff(anom.time.values)).astype("timedelta64[D]")}')
    for d in [mean, cyc, anom, tot]:
        d.close()

    # -- lt vs st: what differs? (line 90, depth, mean)
    print('\n== lt vs st (mean, depth, line 90): summary attr + time coverage')
    for f in ['lt_mean_depth_90.nc', 'st_mean_depth_90.nc']:
        ds = xr.open_dataset(os.path.join(DATA_DIR, f))
        print(f'   {f}:')
        for att in ['summary', 'time_coverage_start', 'time_coverage_end', 'comment']:
            if att in ds.attrs:
                print(f'     {att}: {str(ds.attrs[att])[:200]}')
        ds.close()


def main():
    os.makedirs(CONTEXT_DIR, exist_ok=True)
    df = inventory()
    outfile = os.path.join(CONTEXT_DIR, 'file_inventory.csv')
    df.to_csv(outfile, index=False)
    print(f'Wrote inventory of {len(df)} files to {outfile}')

    print('\n== File counts by group / product')
    print(df.groupby(['group', 'product', 'vcoord']).size().unstack(fill_value=0))
    print('\n== Lines by group')
    print(df.groupby(['group'])['line'].unique())
    print('\n== Titles (unique, truncated)')
    for t in sorted(df['title'].unique()):
        print('  -', t[:120])

    targeted_checks()


if __name__ == '__main__':
    main()
