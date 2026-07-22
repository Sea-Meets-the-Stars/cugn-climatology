"""Shared helpers for CUGN 2026-beta interannual-anomaly (iav_) analysis.

All loaders TRIM the trailing all-NaN 10-day steps that pad the anomaly/total
records past the last valid observation (~today, 2026-07-10).
"""
import os
import numpy as np
import xarray as xr

DATADIR = os.path.join(os.environ["OS_SPRAY"], "CUGN", "Climatology", "2026 beta")
FIGDIR = "/home/xavier/Oceanography/python/cugn-climatology/context/figs"


def fpath(group, product, vcoord, line):
    return os.path.join(DATADIR, f"{group}_{product}_{vcoord}_{line}.nc")


def load_anomaly(group, line, vcoord="depth", var="temperature"):
    """Load one anomaly variable, trimmed of trailing all-NaN time steps.

    Returns the trimmed xr.DataArray (dims time, depth/potential_density,
    distance) and the trimmed Dataset (for coords).
    """
    ds = xr.open_dataset(fpath(group, "anomaly", vcoord, line))
    da = ds[var]
    # spatial dims = everything except time
    sdims = [d for d in da.dims if d != "time"]
    allnan = np.isnan(da).all(dim=sdims)
    keep = ~allnan.values
    ds = ds.isel(time=keep)
    return ds[var], ds


def depth_average(da, zmax=100.0):
    """0-zmax m depth average (depth-coord fields). NaN-aware mean."""
    sub = da.sel(depth=slice(0, zmax))
    return sub.mean(dim="depth", skipna=True)


def line_style():
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.dpi": 120,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "savefig.bbox": "tight",
    })
