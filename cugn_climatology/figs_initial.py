""" Initial descriptive figures for the 2026 beta CUGN climatology.

Generates a small set of figures characterizing the data, written to
context/figs/. Run in the ocean14 conda environment:

    python -m cugn_climatology.figs_initial

Figures:
    fig01_line_geometry.png     Map of the 5 CUGN section lines
    fig02_mean_sections_st90.png  Mean cross-sections (T, S, DO, chl-a), st line 90
    fig03_mean_sigma_st90.png   Mean temperature on potential-density coords
    fig04_annual_cycle_sst.png  Seasonal cycle of near-surface T vs distance
    fig05_anomaly_hovmoller.png Interannual near-surface T anomaly (time x distance)
    fig06_lt_vs_st_mean.png     st minus lt mean temperature section, line 90
"""

import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cmocean
import xarray as xr

DATA_DIR = os.path.join(os.environ['OS_SPRAY'], 'CUGN', 'Climatology', '2026 beta')
FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'context', 'figs')

LINES = ['56', '66', '80', '90', 'al']
LINE_COLORS = dict(zip(LINES, ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#666666']))


def _open(group, product, vcoord, line):
    return xr.open_dataset(os.path.join(DATA_DIR, f'{group}_{product}_{vcoord}_{line}.nc'))


def fig_line_geometry():
    fig, ax = plt.subplots(figsize=(7, 7))
    for ln in LINES:
        ds = _open('st', 'mean', 'depth', ln)
        ax.plot(ds.longitude, ds.latitude, '-', color=LINE_COLORS[ln], lw=2,
                label=f'Line {ln}' if ln != 'al' else 'Alongshore')
        ax.plot(ds.longitude.values[0], ds.latitude.values[0], 'o',
                color=LINE_COLORS[ln], ms=7)  # inshore (distance=0)
        ds.close()
    ax.set_xlabel('Longitude (°E)')
    ax.set_ylabel('Latitude (°N)')
    ax.set_title('CUGN section lines (2026 beta)\nfilled circle = inshore end (distance = 0)')
    ax.legend(loc='upper right')
    ax.set_aspect(1.0 / np.cos(np.deg2rad(34)))
    ax.grid(alpha=0.3)
    _save(fig, 'fig01_line_geometry.png')


def fig_mean_sections_st90():
    ds = _open('st', 'mean', 'depth', '90')
    panels = [('temperature', cmocean.cm.thermal, 'Temperature (°C)'),
              ('salinity', cmocean.cm.haline, 'Salinity (PSS-78)'),
              ('doxy', cmocean.cm.oxy, 'Dissolved oxygen (µmol kg⁻¹)'),
              ('chlorophyll_a', cmocean.cm.algae, 'Chlorophyll-a (mg m⁻³)')]
    fig, axs = plt.subplots(2, 2, figsize=(13, 9), sharex=True, sharey=True)
    for ax, (v, cmap, label) in zip(axs.flat, panels):
        C = ds[v].transpose('depth', 'distance').values
        pc = ax.pcolormesh(ds.distance, ds.depth, C, cmap=cmap, shading='auto')
        fig.colorbar(pc, ax=ax, label=label)
        ax.set_title(v)
    for ax in axs[:, 0]:
        ax.set_ylabel('Depth (m)')
    for ax in axs[-1, :]:
        ax.set_xlabel('Distance offshore (km)')
    axs[0, 0].invert_yaxis()
    fig.suptitle('Short-term mean cross-sections — CUGN Line 90 (depth coords)',
                 fontsize=14)
    ds.close()
    _save(fig, 'fig02_mean_sections_st90.png')


def fig_mean_sigma_st90():
    ds = _open('st', 'mean', 'sigma', '90')
    fig, ax = plt.subplots(figsize=(9, 5))
    C = ds['temperature'].transpose('potential_density', 'distance').values
    pc = ax.pcolormesh(ds.distance, ds.potential_density, C,
                       cmap=cmocean.cm.thermal, shading='auto')
    fig.colorbar(pc, ax=ax, label='Temperature (°C)')
    ax.invert_yaxis()
    ax.set_xlabel('Distance offshore (km)')
    ax.set_ylabel('Potential density σ (kg m⁻³)')
    ax.set_title('Short-term mean temperature on density coordinates — Line 90')
    ds.close()
    _save(fig, 'fig03_mean_sigma_st90.png')


def fig_annual_cycle_sst():
    ds = _open('st', 'mean_annual_cycle', 'depth', '90')
    t10 = ds['temperature'].sel(depth=10)  # near-surface
    # The nominal year runs Jan 10 -> following Jan 9, so calendar day-of-year is
    # not monotonic; reorder to Jan 1 -> Dec 31 for a clean seasonal axis.
    doy = np.array([t.dayofyr for t in ds.time.values])
    order = np.argsort(doy)
    C = t10.transpose('time', 'distance').values[order]
    fig, ax = plt.subplots(figsize=(10, 5))
    pc = ax.pcolormesh(ds.distance, doy[order], C,
                       cmap=cmocean.cm.thermal, shading='auto')
    fig.colorbar(pc, ax=ax, label='Temperature at 10 m (°C)')
    month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    ax.set_yticks(month_starts)
    ax.set_yticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    ax.set_xlabel('Distance offshore (km)')
    ax.set_ylabel('Month (climatological year)')
    ax.set_title('Seasonal cycle of 10 m temperature — CUGN Line 90 (short-term)')
    ds.close()
    _save(fig, 'fig04_annual_cycle_sst.png')


def fig_anomaly_hovmoller():
    ds = _open('st', 'anomaly', 'depth', '90')
    t10 = ds['temperature'].sel(depth=10)
    valid = ~np.isnan(t10).all(dim='distance')  # drop padded all-NaN steps
    t10 = t10.isel(time=valid.values)
    vmax = float(np.nanpercentile(np.abs(t10), 99))
    fig, ax = plt.subplots(figsize=(11, 5))
    C = t10.transpose('distance', 'time').values
    pc = ax.pcolormesh(t10.time, ds.distance, C, cmap=cmocean.cm.balance,
                       vmin=-vmax, vmax=vmax, shading='auto')
    fig.colorbar(pc, ax=ax, label='10 m temperature anomaly (°C)')
    ax.set_xlabel('Time')
    ax.set_ylabel('Distance offshore (km)')
    ax.set_title('Interannual 10 m temperature anomaly — CUGN Line 90 (short-term)')
    ds.close()
    _save(fig, 'fig05_anomaly_hovmoller.png')


def fig_lt_vs_st_mean():
    lt = _open('lt', 'mean', 'depth', '90')
    st = _open('st', 'mean', 'depth', '90')
    diff = (st['temperature'] - lt['temperature']).transpose('depth', 'distance')
    vmax = float(np.nanpercentile(np.abs(diff), 99))
    fig, ax = plt.subplots(figsize=(9, 5))
    pc = ax.pcolormesh(st.distance, st.depth, diff.values, cmap=cmocean.cm.balance,
                       vmin=-vmax, vmax=vmax, shading='auto')
    fig.colorbar(pc, ax=ax, label='ΔT: st − lt (°C)')
    ax.invert_yaxis()
    ax.set_xlabel('Distance offshore (km)')
    ax.set_ylabel('Depth (m)')
    ax.set_title('Mean temperature difference: short-term (2017–2025) − long-term (2007–2014)\nCUGN Line 90')
    lt.close(); st.close()
    _save(fig, 'fig06_lt_vs_st_mean.png')


def _save(fig, name):
    fig.tight_layout()
    outfile = os.path.join(FIG_DIR, name)
    fig.savefig(outfile, dpi=130, bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {outfile}')


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    print(f'Writing figures to {FIG_DIR}')
    fig_line_geometry()
    fig_mean_sections_st90()
    fig_mean_sigma_st90()
    fig_annual_cycle_sst()
    fig_anomaly_hovmoller()
    fig_lt_vs_st_mean()
    print('Done.')


if __name__ == '__main__':
    main()
