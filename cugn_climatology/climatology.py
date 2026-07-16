""" Compute CUGN-style climatologies from a gridded time series.

The 2026 beta products decompose an observed field into three pieces that add
back exactly:

    total(t) = mean + annual_cycle[day-of-year(t)] + anomaly(t)

This module reproduces that methodology from a `total`-like field
(dims: time x vertical x distance):

    mean          time mean over a baseline window
    annual_cycle  harmonic fit (constant + N harmonics at period 365.25 d) of
                  the de-meaned field, evaluated at 365 daily steps and
                  mean-removed (a pure seasonal anomaly cycle)
    anomaly       residual = total - mean - annual_cycle[doy]

Notes / caveats
---------------
- The shipped 2026 beta products were generated from denser Level-3 binned
  glider data, not from the 10-day `total` product. Recomputing from `total`
  therefore *approximates* the shipped fields (annual cycle typically within
  ~5-10% of its amplitude for T; see validate_against_shipped). The point of
  this module is a faithful, self-consistent implementation of the CUGN
  methodology that can be applied to any gridded series.
- Trailing all-NaN time steps (the rolling product pads to end of year) are
  trimmed before computation, per project convention.

Run the built-in validation:
    python -m cugn_climatology.climatology
"""

import os
import warnings

import numpy as np
import pandas as pd
import xarray as xr

# CUGN annual-cycle fundamental period (see cugn/annualcycle.py: 365.25 d).
YEAR_DAYS = 365.25


def _to_datetime(time_values):
    """ Coerce a time coordinate (datetime64, cftime, or int Unix seconds) to
    a pandas DatetimeIndex. """
    v0 = np.asarray(time_values).ravel()[0]
    if np.issubdtype(np.asarray(time_values).dtype, np.integer):
        return pd.to_datetime(time_values, unit='s')
    if hasattr(v0, 'calendar'):  # cftime
        return pd.to_datetime([f'{t.year}-{t.month:02d}-{t.day:02d}'
                               for t in time_values])
    return pd.to_datetime(time_values)


def trim_padding(da, time_dim='time'):
    """ Drop trailing time steps that are entirely NaN (rolling-product pad). """
    other = [d for d in da.dims if d != time_dim]
    allnan = np.isnan(da).all(dim=other)
    valid = np.where(~allnan.values)[0]
    if valid.size == 0:
        return da
    return da.isel({time_dim: slice(0, valid[-1] + 1)})


def _harmonic_design(doy, nharm, period=YEAR_DAYS):
    """ Design matrix [1, sin(kωt), cos(kωt)] for k=1..nharm, ω=2π/period. """
    w = 2.0 * np.pi / period
    cols = [np.ones_like(doy, dtype=float)]
    for k in range(1, nharm + 1):
        cols.append(np.sin(w * k * doy))
        cols.append(np.cos(w * k * doy))
    return np.vstack(cols).T


def compute_climatology(da, baseline=None, nharm=3, time_dim='time',
                        eval_days=365):
    """ Decompose a gridded time series into mean + annual_cycle + anomaly.

    Parameters
    ----------
    da : xr.DataArray
        Dims (time, vertical, distance); vertical is 'depth' or
        'potential_density'. Time may be datetime64, cftime, or int seconds.
    baseline : (start, end) or None
        Window (inclusive start, exclusive end) used to fit mean + annual
        cycle. Strings or timestamps. None -> use the full (trimmed) record.
    nharm : int
        Number of annual harmonics (CUGN uses a few; 2-3 reproduces the
        shipped T cycle to ~5-10% of amplitude).
    eval_days : int
        Number of daily steps for the returned annual cycle (365).

    Returns
    -------
    xr.Dataset with data_vars: mean, annual_cycle (dim day_of_year=1..eval_days),
    anomaly (dim time), total_reconstructed; plus attrs recording the settings.
    """
    da = trim_padding(da, time_dim=time_dim)
    vdim = [d for d in da.dims if d not in (time_dim, 'distance')][0]

    time = _to_datetime(da[time_dim].values)
    doy = time.dayofyear.values.astype(float)

    if baseline is None:
        inwin = np.ones(len(time), dtype=bool)
    else:
        t0 = pd.Timestamp(baseline[0]).tz_localize(None)
        t1 = pd.Timestamp(baseline[1]).tz_localize(None)
        inwin = np.asarray((time >= t0) & (time < t1))

    nt = da.sizes[time_dim]
    nv = da.sizes[vdim]
    nx = da.sizes['distance']
    arr = da.transpose(time_dim, vdim, 'distance').values  # (nt, nv, nx)
    flat = arr.reshape(nt, nv * nx)

    # Baseline mean (all-NaN columns -> NaN; that RuntimeWarning is expected)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        mean_flat = np.nanmean(np.where(inwin[:, None], flat, np.nan), axis=0)

    # Harmonic fit of (field - mean) over the baseline, per column
    demeaned = flat - mean_flat[None, :]
    doy_eval = np.arange(1, eval_days + 1, dtype=float)
    G_fit = _harmonic_design(doy[inwin], nharm)
    G_eval = _harmonic_design(doy_eval, nharm)

    cycle_flat = np.full((eval_days, nv * nx), np.nan)
    y_all = demeaned[inwin]
    for j in range(nv * nx):
        y = y_all[:, j]
        good = np.isfinite(y)
        if good.sum() < 2 * nharm + 2:
            continue
        coef, *_ = np.linalg.lstsq(G_fit[good], y[good], rcond=None)
        fit = G_eval @ coef
        cycle_flat[:, j] = fit - fit.mean()  # mean-removed seasonal cycle

    # Anomaly = field - mean - cycle[doy] over the full (trimmed) record
    idx = (np.rint(doy).astype(int) - 1).clip(0, eval_days - 1)
    anom_flat = flat - mean_flat[None, :] - cycle_flat[idx, :]

    mean = mean_flat.reshape(nv, nx)
    cycle = cycle_flat.reshape(eval_days, nv, nx)
    anom = anom_flat.reshape(nt, nv, nx)

    vcoord = da[vdim]
    out = xr.Dataset(
        data_vars=dict(
            mean=((vdim, 'distance'), mean),
            annual_cycle=(('day_of_year', vdim, 'distance'), cycle),
            anomaly=((time_dim, vdim, 'distance'), anom),
            total_reconstructed=((time_dim, vdim, 'distance'),
                                 mean[None] + cycle[idx] + anom),
        ),
        coords={vdim: vcoord, 'distance': da['distance'],
                'day_of_year': doy_eval.astype(int), time_dim: da[time_dim]},
    )
    out.attrs.update(nharm=nharm, period_days=YEAR_DAYS,
                     baseline_start=str(baseline[0]) if baseline else 'full',
                     baseline_end=str(baseline[1]) if baseline else 'full',
                     source='cugn_climatology.climatology.compute_climatology')
    return out


# Baseline windows implied by the shipped mean `time_coverage_*` attributes.
BASELINE = {'lt': ('2007-01-01', '2014-01-01'),
            'st': ('2017-01-01', '2025-01-01')}


def validate_against_shipped(group='lt', line='90', vcoord='depth',
                             var='temperature', nharm=3, data_dir=None):
    """ Recompute from the shipped `total` and compare to shipped
    mean / annual_cycle / anomaly. Returns a dict of RMS + amplitude stats. """
    if data_dir is None:
        data_dir = os.path.join(os.environ['OS_SPRAY'], 'CUGN',
                                'Climatology', '2026 beta')

    def _open(product):
        return xr.open_dataset(
            os.path.join(data_dir, f'{group}_{product}_{vcoord}_{line}.nc'))

    tot = _open('total')[var]
    clim = compute_climatology(tot, baseline=BASELINE[group], nharm=nharm)

    ship_mean = _open('mean')[var]
    ship_cyc = _open('annual_cycle')[var]

    # annual_cycle: shipped time is Unix seconds -> day-of-year, mean-removed
    cyc_doy = _to_datetime(ship_cyc['time'].values).dayofyear.values
    order = np.argsort(cyc_doy)
    ship_cyc_sorted = ship_cyc.isel(time=order).values
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        ship_cyc_sorted = ship_cyc_sorted - np.nanmean(ship_cyc_sorted, axis=0,
                                                       keepdims=True)

    def rms(a, b):
        return float(np.sqrt(np.nanmean((np.asarray(a) - np.asarray(b)) ** 2)))

    stats = dict(
        group=group, line=line, vcoord=vcoord, var=var, nharm=nharm,
        mean_rms=rms(clim['mean'].values, ship_mean.values),
        mean_amp=float(np.nanstd(ship_mean.values)),
        cycle_rms=rms(clim['annual_cycle'].values, ship_cyc_sorted),
        cycle_amp=float(np.nanstd(ship_cyc_sorted)),
        # Internal additive identity of our own decomposition (should be ~0):
        self_recon_rms=rms(clim['total_reconstructed'].values,
                           trim_padding(tot).transpose('time', vcoord if vcoord == 'depth' else 'potential_density', 'distance').values),
    )
    return stats


def main():
    print('Validating recomputed climatology vs shipped 2026 beta products\n')
    header = f'{"grp":>3} {"line":>4} {"var":>13} | mean_rms  (amp)   cyc_rms  (amp)   self_recon'
    print(header)
    print('-' * len(header))
    for group in ['lt', 'st']:
        for var in ['temperature', 'salinity']:
            s = validate_against_shipped(group=group, line='90',
                                         var=var, nharm=3)
            print(f'{s["group"]:>3} {s["line"]:>4} {s["var"]:>13} | '
                  f'{s["mean_rms"]:.4f} ({s["mean_amp"]:.3f})   '
                  f'{s["cycle_rms"]:.4f} ({s["cycle_amp"]:.3f})   '
                  f'{s["self_recon_rms"]:.2e}')
    print('\nmean_rms/cyc_rms are recomputed-vs-shipped differences (shipped '
          'came from denser input, so nonzero is expected).\n'
          'self_recon ~0 confirms our own mean+cycle+anomaly adds back exactly.')


if __name__ == '__main__':
    main()
