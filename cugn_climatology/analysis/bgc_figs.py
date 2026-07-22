"""BGC figures for CUGN 2026 beta climatology (dissolved oxygen, chl, backscatter)."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import cmocean
import pandas as pd

from bgc_common import open_ds, trim_trailing_nan, FIGDIR, HYPOXIC, SEVERE

os.makedirs(FIGDIR, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'figure.dpi': 120})


def savef(fig, name):
    fp = os.path.join(FIGDIR, name)
    fig.savefig(fp, bbox_inches='tight', dpi=140)
    plt.close(fig)
    print("wrote", fp)


# ------------------------------------------------------------------
# FIG 1: Line 90 mean sections — doxy, chl, backscatter
# ------------------------------------------------------------------
def fig_mean_sections():
    ds = open_ds('st', 'mean', 'depth', '90')
    dist = ds['distance'].values
    depth = ds['depth'].values
    sig = ds['sigma_t'].values
    X, Z = np.meshgrid(dist, depth)

    fig, axs = plt.subplots(3, 1, figsize=(8.5, 10), sharex=True)

    # doxy
    ax = axs[0]
    doxy = np.ma.masked_invalid(ds['doxy'].values)
    pc = ax.pcolormesh(X, Z, doxy, cmap=cmocean.cm.oxy, vmin=0, vmax=280, shading='auto')
    cs = ax.contour(X, Z, np.ma.masked_invalid(ds['doxy'].values),
                    levels=[SEVERE, HYPOXIC, 120], colors='k', linewidths=[1.4, 1.4, 0.7],
                    linestyles=['--', '-', ':'])
    ax.clabel(cs, fmt='%.0f', fontsize=8)
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('doxy [umol kg$^{-1}$]')
    ax.set_title('(a) Dissolved oxygen  (solid=60 hypoxic, dashed=22 severe)')
    ax.set_ylabel('depth [m]')

    # chl
    ax = axs[1]
    chl = np.ma.masked_invalid(ds['chlorophyll_a'].values)
    pc = ax.pcolormesh(X, Z, chl, cmap=cmocean.cm.algae, vmin=0, vmax=1.0, shading='auto')
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('chl-a [mg m$^{-3}$]')
    # SCM depth line
    u = depth <= 150
    scm = []
    for j in range(chl.shape[1]):
        col = ds['chlorophyll_a'].values[u, j]
        scm.append(depth[u][np.nanargmax(col)] if np.isfinite(col).any() else np.nan)
    ax.plot(dist, scm, 'w-', lw=1.5, label='SCM depth')
    ax.legend(loc='lower right', fontsize=8)
    ax.set_title('(b) Chlorophyll-a (white = subsurface chl max)')
    ax.set_ylabel('depth [m]')
    ax.set_ylim(0, 200)

    # backscatter
    ax = axs[2]
    bs = np.ma.masked_invalid(ds['acoustic_backscatter'].values)
    pc = ax.pcolormesh(X, Z, bs, cmap=cmocean.cm.matter, vmin=57, vmax=70, shading='auto')
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('backscatter [dB]')
    ax.set_title('(c) Acoustic backscatter (uncalibrated)')
    ax.set_ylabel('depth [m]')
    ax.set_xlabel('cross-shore distance [km]  (0 = inshore)')

    for ax in axs:
        ax.invert_yaxis()
    axs[0].set_ylim(500, 0)
    axs[2].set_ylim(500, 0)
    fig.suptitle('CUGN Line 90 — short-term mean BGC sections (2017–2025)', y=0.995)
    savef(fig, 'bgc_mean_sections_90.png')
    ds.close()


# ------------------------------------------------------------------
# FIG 2: latitudinal variation of the OMZ across lines
# ------------------------------------------------------------------
def fig_alonglines():
    lines = ['56', '66', '80', '90']
    fig, axs = plt.subplots(2, 2, figsize=(11, 8), sharey=True)
    axs = axs.ravel()
    pc = None
    for ax, line in zip(axs, lines):
        ds = open_ds('st', 'mean', 'depth', line)
        dist = ds['distance'].values
        depth = ds['depth'].values
        X, Z = np.meshgrid(dist, depth)
        doxy = np.ma.masked_invalid(ds['doxy'].values)
        pc = ax.pcolormesh(X, Z, doxy, cmap=cmocean.cm.oxy, vmin=0, vmax=280, shading='auto')
        cs = ax.contour(X, Z, ds['doxy'].values, levels=[SEVERE, HYPOXIC],
                        colors='k', linewidths=[1.2, 1.4], linestyles=['--', '-'])
        ax.clabel(cs, fmt='%.0f', fontsize=7)
        ax.set_title(f'Line {line}')
        ax.set_ylim(500, 0)
        ax.set_xlabel('distance [km]')
        ds.close()
    axs[0].set_ylabel('depth [m]'); axs[2].set_ylabel('depth [m]')
    cb = fig.colorbar(pc, ax=axs, pad=0.02, shrink=0.85)
    cb.set_label('doxy [umol kg$^{-1}$]')
    fig.suptitle('Cross-shore dissolved-oxygen sections by line (N→S: 56,66,80,90)\n'
                 'OMZ intensifies and hypoxia (60) shoals to the south', y=1.02)
    savef(fig, 'bgc_omz_alonglines.png')


# ------------------------------------------------------------------
# FIG 3: oxygen on isopycnals
# ------------------------------------------------------------------
def fig_isopycnals():
    ds = open_ds('st', 'mean', 'sigma', '90')
    dist = ds['distance'].values
    pd_ = ds['potential_density'].values
    doxy = ds['doxy'].values          # (density, distance)
    zdepth = ds['depth'].values       # mean depth of each isopycnal (density, distance)

    dsz = open_ds('st', 'mean', 'depth', '90')
    zlev = dsz['depth'].values
    doxy_z = dsz['doxy'].values       # (depth, distance)

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    # (a) doxy on density surfaces
    ax = axs[0]
    X, Y = np.meshgrid(dist, pd_)
    pc = ax.pcolormesh(X, Y, np.ma.masked_invalid(doxy), cmap=cmocean.cm.oxy,
                       vmin=0, vmax=280, shading='auto')
    cs = ax.contour(X, Y, doxy, levels=[SEVERE, HYPOXIC], colors='k',
                    linewidths=[1.2, 1.4], linestyles=['--', '-'])
    ax.clabel(cs, fmt='%.0f', fontsize=8)
    ax.invert_yaxis()
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('doxy [umol kg$^{-1}$]')
    ax.set_xlabel('distance [km]'); ax.set_ylabel('potential density [kg m$^{-3}$]')
    ax.set_title('(a) Line 90 doxy on isopycnals')

    # (b) cross-shore spread of doxy on depth vs on density surfaces
    ax = axs[1]
    std_z = np.nanstd(doxy_z, axis=1)                 # per depth level
    std_s = np.nanstd(doxy, axis=1)                   # per density level
    zmean_s = np.nanmean(zdepth, axis=1)              # mean depth of each isopycnal
    ax.plot(std_z, zlev, 'k-o', ms=3, lw=1.3, label='on depth surfaces')
    ax.plot(std_s, zmean_s, '-s', color='tab:blue', ms=3, lw=1.3,
            label='on density surfaces')
    ax.set_ylim(500, 0)
    ax.set_xlabel('cross-shore std of doxy [umol kg$^{-1}$]')
    ax.set_ylabel('depth [m]  (density mapped to mean depth)')
    ax.set_title('(b) Cross-shore variability of oxygen\nis smaller on isopycnals')
    ax.legend(fontsize=9); ax.grid(alpha=0.3)

    fig.suptitle('Line 90: oxygen is more tightly organized on density surfaces than depth',
                 y=1.04)
    savef(fig, 'bgc_oxygen_isopycnals_90.png')
    ds.close(); dsz.close()


# ------------------------------------------------------------------
# FIG 4: seasonal cycle (Line 90)
# ------------------------------------------------------------------
def fig_seasonal():
    ds = open_ds('st', 'mean_annual_cycle', 'depth', '90')
    dist = ds['distance'].values
    depth = ds['depth'].values
    doy = np.arange(1, ds.sizes['time'] + 1)  # nominal 365-day climatological year
    # fixed distance ~150 km
    j = np.argmin(np.abs(dist - 150))
    doxy = ds['doxy'].values[:, :, j]   # (time, depth)

    # annual_cycle (anomaly form) for amplitude
    dsa = open_ds('st', 'annual_cycle', 'depth', '90')
    doxy_a = dsa['doxy'].values[:, :, j]

    fig, axs = plt.subplots(1, 2, figsize=(13, 5))

    ax = axs[0]
    T, Z = np.meshgrid(doy, depth, indexing='ij')
    pc = ax.pcolormesh(T, Z, np.ma.masked_invalid(doxy), cmap=cmocean.cm.oxy,
                       vmin=0, vmax=280, shading='auto')
    cs = ax.contour(T, Z, doxy, levels=[HYPOXIC], colors='k', linewidths=1.4)
    ax.clabel(cs, fmt='%.0f', fontsize=8)
    ax.invert_yaxis(); ax.set_ylim(500, 0)
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('doxy [umol kg$^{-1}$]')
    ax.set_xlabel('day of year'); ax.set_ylabel('depth [m]')
    ax.set_title(f'(a) Seasonal mean doxy at dist~{dist[j]:.0f} km')

    ax = axs[1]
    amp = np.nanmax(doxy_a, axis=0) - np.nanmin(doxy_a, axis=0)
    T, Z = np.meshgrid(doy, depth, indexing='ij')
    pc = ax.pcolormesh(T, Z, np.ma.masked_invalid(doxy_a), cmap=cmocean.cm.balance,
                       vmin=-30, vmax=30, shading='auto')
    ax.invert_yaxis(); ax.set_ylim(300, 0)
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('doxy anomaly [umol kg$^{-1}$]')
    ax.set_xlabel('day of year'); ax.set_ylabel('depth [m]')
    ax.set_title('(b) Seasonal doxy anomaly (annual_cycle)')

    fig.suptitle('CUGN Line 90 — seasonal cycle of dissolved oxygen', y=1.02)
    savef(fig, 'bgc_seasonal_90.png')
    ds.close(); dsa.close()


# ------------------------------------------------------------------
# FIG 5: interannual anomaly + trend (Line 90)
# ------------------------------------------------------------------
def fig_interannual():
    ds = trim_trailing_nan(open_ds('st', 'anomaly', 'depth', '90'))
    t = pd.to_datetime(ds['time'].values)
    depth = ds['depth'].values
    doxy = ds['doxy'].values         # (time, depth, distance)
    prof = np.nanmean(doxy, axis=2)  # (time, depth)

    tnum = (t - t[0]).days.values / 365.25
    trend = np.full(len(depth), np.nan)
    for k in range(len(depth)):
        y = prof[:, k]
        m = np.isfinite(y)
        if m.sum() > 20:
            trend[k] = np.polyfit(tnum[m], y[m], 1)[0]

    fig, axs = plt.subplots(1, 2, figsize=(13, 5),
                            gridspec_kw={'width_ratios': [3, 1]})
    ax = axs[0]
    T, Z = np.meshgrid(mdates.date2num(t), depth, indexing='ij')
    pc = ax.pcolormesh(T, Z, np.ma.masked_invalid(prof), cmap=cmocean.cm.balance,
                       vmin=-40, vmax=40, shading='auto')
    ax.invert_yaxis(); ax.set_ylim(500, 0)
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('doxy anomaly [umol kg$^{-1}$]')
    ax.set_ylabel('depth [m]'); ax.set_xlabel('year')
    ax.set_title('(a) Line 90 interannual doxy anomaly (line-averaged)')

    ax = axs[1]
    ax.plot(trend * 10, depth, 'b-')  # per decade
    ax.axvline(0, color='k', lw=0.7)
    ax.invert_yaxis(); ax.set_ylim(500, 0)
    ax.set_xlabel('trend [umol kg$^{-1}$ decade$^{-1}$]')
    ax.set_title('(b) 2017–2026 linear trend')
    ax.grid(alpha=0.3)

    fig.suptitle('CUGN Line 90 — interannual dissolved-oxygen variability & trend', y=1.0)
    savef(fig, 'bgc_interannual_90.png')
    ds.close()


# ------------------------------------------------------------------
# FIG 6: acoustic backscatter structure & seasonality (Line 90)
# ------------------------------------------------------------------
def fig_backscatter():
    ds = open_ds('st', 'mean', 'depth', '90')
    depth = ds['depth'].values
    dist = ds['distance'].values
    bs = ds['acoustic_backscatter'].values

    dsm = open_ds('st', 'mean_annual_cycle', 'depth', '90')
    doy = np.arange(1, dsm.sizes['time'] + 1)
    j = np.argmin(np.abs(dist - 150))
    bs_seas = dsm['acoustic_backscatter'].values[:, :, j]

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    ax = axs[0]
    for jj in range(0, bs.shape[1], 8):
        ax.plot(bs[:, jj], depth, color='0.75', lw=0.6)
    ax.plot(np.nanmedian(bs, axis=1), depth, 'r-', lw=2, label='line median')
    ax.invert_yaxis(); ax.set_ylim(500, 0)
    ax.set_xlabel('backscatter [dB]'); ax.set_ylabel('depth [m]')
    ax.set_title('(a) Vertical structure (grey=stations)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axs[1]
    T, Z = np.meshgrid(doy, depth, indexing='ij')
    pc = ax.pcolormesh(T, Z, np.ma.masked_invalid(bs_seas), cmap=cmocean.cm.matter,
                       vmin=57, vmax=70, shading='auto')
    ax.invert_yaxis(); ax.set_ylim(300, 0)
    cb = fig.colorbar(pc, ax=ax, pad=0.02); cb.set_label('backscatter [dB]')
    ax.set_xlabel('day of year'); ax.set_ylabel('depth [m]')
    ax.set_title(f'(b) Seasonal cycle at dist~{dist[j]:.0f} km')

    fig.suptitle('CUGN Line 90 — acoustic backscatter (zooplankton/particle proxy)', y=1.02)
    savef(fig, 'bgc_backscatter_90.png')
    ds.close(); dsm.close()


if __name__ == '__main__':
    fig_mean_sections()
    fig_alonglines()
    fig_isopycnals()
    fig_seasonal()
    fig_interannual()
    fig_backscatter()
    print("done")
