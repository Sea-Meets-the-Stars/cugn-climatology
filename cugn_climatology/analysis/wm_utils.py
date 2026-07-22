"""Shared helpers for water-mass / T-S / stratification / spiciness analysis
of the CUGN 2026-beta climatology (wm_ series).

Run figure scripts in the ocean14 conda environment, e.g.

    python -m cugn_climatology.analysis.wm_ts_analysis

All derived thermodynamic quantities use TEOS-10 (the `gsw` package):
Absolute Salinity (SA), Conservative Temperature (CT), spiciness0, and N^2.
The climatology stores in-situ `temperature` (ITS-90), practical `salinity`
(PSS-78), and `potential_density` (sigma-theta).
"""
import os

import numpy as np
import xarray as xr
import gsw

DDIR = os.path.join(os.environ['OS_SPRAY'], 'CUGN', 'Climatology', '2026 beta')
FIGDIR = '/home/xavier/Oceanography/python/cugn-climatology/context/figs'

# Cross-shore lines, ordered N -> S (56 northernmost, 90 off San Diego).
# 'al' is the alongshore line (runs S->N, not offshore).
LINES = ['56', '66', '80', '90', 'al']
XSHORE = ['56', '66', '80', '90']

# Approximate central latitude of each line (for labelling / ordering).
LINE_LAT = {'56': 37.8, '66': 36.0, '80': 33.6, '90': 32.3, 'al': 33.3}

# Qualitative, colour-blind-safe line palette (ColorBrewer Dark2).
LINE_COLORS = {
    '56': '#1b9e77', '66': '#d95f02', '80': '#7570b3',
    '90': '#e7298a', 'al': '#666666',
}
LINE_LABEL = {
    '56': 'Line 56 (N)', '66': 'Line 66', '80': 'Line 80',
    '90': 'Line 90 (S)', 'al': 'Alongshore',
}


def path(group, product, vcoord, line):
    return os.path.join(DDIR, f'{group}_{product}_{vcoord}_{line}.nc')


def open_ds(group, product, vcoord, line):
    return xr.open_dataset(path(group, product, vcoord, line))


def add_teos10(ds):
    """Add SA, CT, spice (spiciness0) and pressure to a depth-coord mean ds.

    Uses the 1-D latitude/longitude(distance) coords broadcast over depth.
    Returns the dataset with new variables:
        pressure  (depth)                dbar
        SA        (depth, distance)      g/kg   Absolute Salinity
        CT        (depth, distance)      degC   Conservative Temperature
        spice     (depth, distance)      kg/m3  spiciness referenced to 0 dbar
    """
    lat = ds['latitude']              # (distance,)
    lon = ds['longitude']             # (distance,)
    # pressure from depth (positive down) at the line's mean latitude
    p1d = gsw.p_from_z(-ds['depth'], float(lat.mean()))     # (depth,)
    p = p1d.broadcast_like(ds['temperature'])
    SA = gsw.SA_from_SP(ds['salinity'], p, lon, lat)
    CT = gsw.CT_from_t(SA, ds['temperature'], p)
    spice = gsw.spiciness0(SA, CT)
    ds = ds.assign(pressure=p1d, SA=SA, CT=CT, spice=spice)
    for name, ln, un in [('SA', 'Absolute Salinity', 'g kg-1'),
                         ('CT', 'Conservative Temperature', 'degree_C'),
                         ('spice', 'Spiciness (ref 0 dbar)', 'kg m-3')]:
        ds[name].attrs.update(long_name=ln, units=un)
    return ds


def buoyancy_frequency(ds):
    """Squared buoyancy frequency N^2 (s^-2) on a depth-coord mean ds.

    Computed with gsw.Nsquared from SA, CT, pressure; returned interpolated
    back onto the original depth grid (midpoint values -> nearest depth).
    Requires add_teos10() to have been called first.
    Returns a DataArray (depth, distance).
    """
    lat = ds['latitude']
    p = ds['pressure'].broadcast_like(ds['CT']).transpose('depth', 'distance').values
    SA = ds['SA'].transpose('depth', 'distance').values
    CT = ds['CT'].transpose('depth', 'distance').values
    latb = np.broadcast_to(lat.values, SA.shape)
    n2 = np.full_like(SA, np.nan)
    z = ds['depth'].values
    for j in range(SA.shape[1]):
        col = np.isfinite(SA[:, j]) & np.isfinite(CT[:, j])
        if col.sum() < 3:
            continue
        zsel = z[col]
        n2mid, _ = gsw.Nsquared(SA[col, j], CT[col, j], p[col, j], latb[col, j])
        zmid = 0.5 * (zsel[:-1] + zsel[1:])
        n2[:, j] = np.interp(z, zmid, n2mid, left=np.nan, right=np.nan)
    return xr.DataArray(n2, coords={'depth': ds['depth'], 'distance': ds['distance']},
                        dims=('depth', 'distance'), name='N2',
                        attrs={'long_name': 'Buoyancy frequency squared',
                               'units': 's-2'})


def apply_style():
    import matplotlib as mpl
    mpl.rcParams.update({
        'figure.dpi': 130,
        'savefig.dpi': 150,
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'legend.fontsize': 8.5,
        'savefig.bbox': 'tight',
    })


def ts_density_grid(ax, slim, tlim, color='0.6'):
    """Overlay sigma-theta contours on a T (CT) vs S (SA) diagram axis."""
    sg = np.linspace(slim[0], slim[1], 120)
    tg = np.linspace(tlim[0], tlim[1], 120)
    SS, TT = np.meshgrid(sg, tg)
    sigma = gsw.sigma0(SS, TT)
    cs = ax.contour(SS, TT, sigma, levels=np.arange(22, 28.1, 0.5),
                    colors=color, linewidths=0.6, alpha=0.8, zorder=1)
    ax.clabel(cs, fmt='%.1f', fontsize=7, inline=True)
    return cs
