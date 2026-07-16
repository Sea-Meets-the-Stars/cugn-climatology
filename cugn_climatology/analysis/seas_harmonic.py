"""Harmonic (annual + semiannual) fit to the CUGN 2026-beta annual_cycle fields.

The `annual_cycle` product is the daily climatological cycle in ANOMALY form
(annual mean removed), on a monotonic day-of-year axis (Jan 1 -> Dec 31, 365
daily steps). The time coordinate is stored as raw epoch seconds with a
non-standard `time:units` attribute, so it must be read with decode_times=False.

For every (depth/sigma level, cross-shore distance) grid point we fit

    y(t) = A0 + a1 cos(w t) + b1 sin(w t) + a2 cos(2 w t) + b2 sin(2 w t)

with w = 2*pi/365 and t = day-of-year - 1.  From the fit we derive
    annual amplitude  = sqrt(a1^2 + b1^2)
    semiannual amp    = sqrt(a2^2 + b2^2)
    phase (day of max of the annual harmonic) -> month of maximum
    fraction of cycle variance explained by the two harmonics.

Utilities here are imported by the figure scripts (seas_figs_*.py).
"""
import os
import numpy as np
import xarray as xr

DATADIR = os.path.join(os.environ['OS_SPRAY'], 'CUGN/Climatology/2026 beta')
FIGDIR = '/home/xavier/Oceanography/python/cugn-climatology/context/figs'

W = 2.0 * np.pi / 365.0


def load_annual_cycle(group, vcoord, line):
    """Open an annual_cycle file with the time axis decoded to day-of-year.

    Returns (ds, doy) where doy is 1..365 in the stored order (monotonic).
    """
    fn = f'{group}_annual_cycle_{vcoord}_{line}.nc'
    ds = xr.open_dataset(os.path.join(DATADIR, fn), decode_times=False)
    t = ds['time'].values.astype('int64')
    doy = ((t - t[0]) // 86400 + 1).astype(int)  # 1..365
    return ds, doy


def harmonic_fit(cycle, doy):
    """Fit annual+semiannual harmonics along the leading (time) axis.

    Parameters
    ----------
    cycle : ndarray, shape (365, ...) - the annual_cycle field (anomaly form).
    doy   : ndarray, shape (365,) - day of year for each time step.

    Returns dict of ndarrays each shaped like cycle[0] (the spatial grid):
      amp1  annual amplitude (same units as field)
      amp2  semiannual amplitude
      phase_doy   day-of-year of the annual-harmonic maximum (1..365)
      month_max   month (1..12) of the annual-harmonic maximum
      frac_var    fraction of the cycle variance explained by both harmonics
      a1,b1,a2,b2 raw coefficients
    """
    t = doy - 1.0
    X = np.column_stack([
        np.ones_like(t),
        np.cos(W * t), np.sin(W * t),
        np.cos(2 * W * t), np.sin(2 * W * t),
    ])  # (365, 5)

    nt = cycle.shape[0]
    spatial_shape = cycle.shape[1:]
    Y = cycle.reshape(nt, -1)  # (365, Npts)

    valid = np.isfinite(Y).all(axis=0)  # columns fully finite
    npts = Y.shape[1]
    coef = np.full((5, npts), np.nan)
    if valid.any():
        beta, *_ = np.linalg.lstsq(X, Y[:, valid], rcond=None)
        coef[:, valid] = beta

    a0, a1, b1, a2, b2 = coef
    amp1 = np.sqrt(a1**2 + b1**2)
    amp2 = np.sqrt(a2**2 + b2**2)

    # phase: y_annual = amp1 * cos(w t - phi); max at w t = phi
    phi = np.arctan2(b1, a1)  # radians
    tmax = (phi / W) % 365.0
    phase_doy = tmax + 1.0

    # variance explained (suppress all-NaN column warnings)
    fit = X @ coef  # (365, npts)
    resid = Y - fit
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        var_tot = np.nanvar(Y, axis=0)
        var_res = np.nanvar(resid, axis=0)
        with np.errstate(invalid='ignore', divide='ignore'):
            frac_var = 1.0 - var_res / var_tot

    # month of max from day-of-year (use a non-leap calendar month layout)
    month_len = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    month_edges = np.concatenate([[0], np.cumsum(month_len)])  # 0..365
    month_max = np.full(npts, np.nan)
    good = np.isfinite(phase_doy)
    month_max[good] = np.digitize(phase_doy[good] - 1, month_edges[1:], right=False) + 1

    def rs(x):
        return x.reshape(spatial_shape)

    return {
        'amp1': rs(amp1), 'amp2': rs(amp2),
        'phase_doy': rs(phase_doy), 'month_max': rs(month_max),
        'frac_var': rs(frac_var),
        'a1': rs(a1), 'b1': rs(b1), 'a2': rs(a2), 'b2': rs(b2),
    }


def efolding_depth(depth, amp_profile):
    """Fit amp(z) = A0 * exp(-z/H) to a 1-D amplitude profile; return H (m).

    Uses log-linear regression on finite, positive amplitudes.
    """
    z = np.asarray(depth, float)
    a = np.asarray(amp_profile, float)
    m = np.isfinite(a) & (a > 0) & np.isfinite(z)
    if m.sum() < 3:
        return np.nan, np.nan
    slope, intercept = np.polyfit(z[m], np.log(a[m]), 1)
    H = -1.0 / slope if slope < 0 else np.nan
    A0 = np.exp(intercept)
    return H, A0


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


if __name__ == '__main__':
    # quick sanity check
    ds, doy = load_annual_cycle('st', 'depth', '90')
    res = harmonic_fit(ds['temperature'].values, doy)
    d = ds['depth'].values
    dist = ds['distance'].values
    i10 = 0  # 10 m
    print('Line 90 st, 10 m temperature annual amplitude vs distance (first 6):')
    print(np.round(res['amp1'][i10, :6], 3))
    print('month of max at 10 m (first 6):', res['month_max'][i10, :6])
    # surface amplitude, offshore-averaged profile
    prof = np.nanmean(res['amp1'], axis=1)
    H, A0 = efolding_depth(d, prof)
    print(f'T annual amp e-folding depth (dist-avg): {H:.1f} m, surface {A0:.2f} C')
