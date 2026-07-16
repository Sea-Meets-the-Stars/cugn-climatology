"""Shared helpers for BGC analysis of CUGN 2026 beta climatology."""
import os
import numpy as np
import xarray as xr

DDIR = os.path.join(os.environ['OS_SPRAY'], 'CUGN', 'Climatology', '2026 beta')
FIGDIR = '/home/xavier/Oceanography/python/cugn-climatology/context/figs'


def path(group, product, vcoord, line):
    return os.path.join(DDIR, f'{group}_{product}_{vcoord}_{line}.nc')


def open_ds(group, product, vcoord, line):
    return xr.open_dataset(path(group, product, vcoord, line))


def trim_trailing_nan(ds, var='doxy'):
    """Drop trailing all-NaN time steps based on `var`."""
    da = ds[var]
    axes = tuple(i for i, d in enumerate(da.dims) if d != 'time')
    allnan = np.isnan(da.values).all(axis=axes)
    valid = np.where(~allnan)[0]
    if len(valid) == 0:
        return ds
    last = valid[-1]
    return ds.isel(time=slice(0, last + 1))


HYPOXIC = 60.0      # umol/kg, common hypoxia threshold
SEVERE = 22.0       # umol/kg, ~ severe hypoxia / near-anoxic proxy (1.5 ml/L ~ 60; 0.5 ml/L ~ 22)
