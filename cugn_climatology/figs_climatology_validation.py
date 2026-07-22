""" Validation figure: recomputed climatology vs shipped 2026 beta products.

Recomputes mean + annual_cycle + anomaly from the shipped `total` field using
cugn_climatology.climatology and compares to the shipped mean / annual_cycle,
for CUGN Line 90 temperature. Writes context/figs/clim_validation.png.

    python -m cugn_climatology.figs_climatology_validation
"""

import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cmocean
import xarray as xr
import pandas as pd

from cugn_climatology.climatology import (compute_climatology, trim_padding,
                                          BASELINE, _to_datetime)

DATA_DIR = os.path.join(os.environ['OS_SPRAY'], 'CUGN', 'Climatology', '2026 beta')
FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'context', 'figs')


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    group, line, var = 'st', '90', 'temperature'

    tot = xr.open_dataset(os.path.join(DATA_DIR, f'{group}_total_depth_{line}.nc'))[var]
    clim = compute_climatology(tot, baseline=BASELINE[group], nharm=3)

    ship_mean = xr.open_dataset(os.path.join(DATA_DIR, f'{group}_mean_depth_{line}.nc'))[var]
    ship_cyc = xr.open_dataset(os.path.join(DATA_DIR, f'{group}_annual_cycle_depth_{line}.nc'))[var]
    cyc_doy = _to_datetime(ship_cyc['time'].values).dayofyear.values
    ship_cyc = ship_cyc.isel(time=np.argsort(cyc_doy))
    ship_cyc = ship_cyc - ship_cyc.mean('time')

    dist, depth = ship_mean.distance.values, ship_mean.depth.values

    fig, axs = plt.subplots(2, 3, figsize=(16, 8))

    # Row 1: mean (shipped, recomputed, diff)
    vmin, vmax = np.nanmin(ship_mean), np.nanmax(ship_mean)
    for ax, field, title in [
            (axs[0, 0], ship_mean.values, 'Shipped mean'),
            (axs[0, 1], clim['mean'].values, 'Recomputed mean')]:
        pc = ax.pcolormesh(dist, depth, field, cmap=cmocean.cm.thermal,
                           vmin=vmin, vmax=vmax, shading='auto')
        fig.colorbar(pc, ax=ax, label='°C'); ax.set_title(title)
    d = clim['mean'].values - ship_mean.values
    pc = axs[0, 2].pcolormesh(dist, depth, d, cmap=cmocean.cm.balance,
                              vmin=-0.3, vmax=0.3, shading='auto')
    fig.colorbar(pc, ax=axs[0, 2], label='°C')
    axs[0, 2].set_title(f'Mean difference (RMS={np.sqrt(np.nanmean(d**2)):.3f} °C)')

    # Row 2: annual cycle at a near-surface, mid-shore point + amplitude map
    iz, ix = 0, 50
    axs[1, 0].plot(clim['day_of_year'], ship_cyc.isel(depth=iz, distance=ix),
                   label='shipped', lw=2)
    axs[1, 0].plot(clim['day_of_year'], clim['annual_cycle'].isel(depth=iz, distance=ix),
                   '--', label='recomputed (3 harm.)', lw=2)
    axs[1, 0].set_xlabel('Day of year'); axs[1, 0].set_ylabel('T anomaly (°C)')
    axs[1, 0].set_title(f'Annual cycle @ {depth[iz]:.0f} m, {dist[ix]:.0f} km')
    axs[1, 0].legend(); axs[1, 0].grid(alpha=0.3)

    amp_ship = ship_cyc.std('time').values
    amp_recon = clim['annual_cycle'].std('day_of_year').values
    for ax, amp, title in [(axs[1, 1], amp_ship, 'Shipped cycle amplitude'),
                           (axs[1, 2], amp_recon, 'Recomputed cycle amplitude')]:
        pc = ax.pcolormesh(dist, depth, amp, cmap=cmocean.cm.amp,
                           vmin=0, vmax=np.nanpercentile(amp_ship, 99), shading='auto')
        fig.colorbar(pc, ax=ax, label='°C'); ax.set_title(title)

    for ax in [axs[0, 0], axs[0, 1], axs[0, 2], axs[1, 1], axs[1, 2]]:
        ax.invert_yaxis(); ax.set_xlabel('Distance (km)'); ax.set_ylabel('Depth (m)')

    fig.suptitle(f'Climatology recomputation vs shipped — {group} Line {line} {var}',
                 fontsize=14)
    fig.tight_layout()
    outfile = os.path.join(FIG_DIR, 'clim_validation.png')
    fig.savefig(outfile, dpi=130, bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {outfile}')


if __name__ == '__main__':
    main()
