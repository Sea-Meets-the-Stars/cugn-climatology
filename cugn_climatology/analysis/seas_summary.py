"""Print a quantitative summary of the seasonal (annual) cycle across all
CUGN lines using harmonic fits to the depth-coordinate annual_cycle files.

Reports, per group/line/variable:
  - near-surface (10 m) annual amplitude, cross-shore averaged and its range
  - month of maximum at 10 m (cross-shore modal)
  - upper-ocean e-folding depth (fit over 10-150 m) of the annual amplitude
  - fraction of grid points where amp1 (annual) exceeds amp2 (semiannual)
"""
import numpy as np
from scipy import stats
import seas_harmonic as sh

GROUPS_LINES = {
    'lt': ['66', '80', '90'],
    'st': ['56', '66', '80', '90', 'al'],
}
VARS = ['temperature', 'salinity', 'chlorophyll_a', 'doxy']


def upper_efold(depth, amp2d, zmax=150.0):
    """Cross-shore-averaged amplitude profile e-folding depth over 10..zmax m."""
    prof = np.nanmean(amp2d, axis=1)
    m = depth <= zmax
    H, A0 = sh.efolding_depth(depth[m], prof[m])
    return H, A0, prof


def modal_month(month2d, depth, z=10.0):
    iz = int(np.argmin(np.abs(depth - z)))
    row = month2d[iz, :]
    row = row[np.isfinite(row)].astype(int)
    if row.size == 0:
        return np.nan
    return stats.mode(row, keepdims=False).mode


for group, lines in GROUPS_LINES.items():
    for line in lines:
        ds, doy = sh.load_annual_cycle(group, 'depth', line)
        depth = ds['depth'].values
        iz10 = int(np.argmin(np.abs(depth - 10.0)))
        print(f'\n=== {group} line {line} ===')
        for v in VARS:
            if v not in ds:
                continue
            res = sh.harmonic_fit(ds[v].values, doy)
            amp1 = res['amp1']
            a10 = amp1[iz10, :]
            a10 = a10[np.isfinite(a10)]
            H, A0, prof = upper_efold(depth, amp1)
            mm = modal_month(res['month_max'], depth, 10.0)
            frac_ann_dom = np.nanmean((amp1 > res['amp2']).astype(float))
            units = ds[v].attrs.get('units', '')
            print(f'  {v:14s} 10m amp mean={np.nanmean(a10):.3g} '
                  f'range=[{np.nanmin(a10):.3g},{np.nanmax(a10):.3g}] {units:10s} '
                  f'| Hefold(10-150m)={H:.0f} m | monthmax(10m)={sh.MONTHS[int(mm)-1] if np.isfinite(mm) else "?"} '
                  f'| ann>semi frac={frac_ann_dom:.2f}')
