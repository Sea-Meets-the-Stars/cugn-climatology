"""Stratification of the CUGN 2026-beta mean fields (short-term group).

Squared buoyancy frequency N^2 = -(g/rho) drho/dz is computed with TEOS-10
(gsw.Nsquared) from the mean SA/CT fields.

Produces:
    wm_stratification.png  Cross-sections of log10(N^2) for the four cross-shore
                           lines (56/66/80/90), with mean sigma-theta contours
                           overlaid; plus a summary panel of the pycnocline
                           depth (depth of maximum N^2) vs distance for all lines.

Run:
    python -m cugn_climatology.analysis.wm_stratification
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cmocean.cm as cmo

from cugn_climatology.analysis import wm_utils as U


def _load(line):
    ds = U.add_teos10(U.open_ds('st', 'mean', 'depth', line))
    ds = ds.assign(N2=U.buoyancy_frequency(ds))
    return ds


def fig_stratification():
    lines = U.XSHORE
    dsets = {ln: _load(ln) for ln in lines}
    # also load alongshore for the summary panel
    dsets['al'] = _load('al')

    fig = plt.figure(figsize=(13, 9))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.9], hspace=0.38, wspace=0.18)

    # N^2 in s^-2; plot log10. Typical pycnocline N^2 ~ 1e-3 .. 1e-4.
    vmin, vmax = -5.0, -3.3
    axes = []
    for i, ln in enumerate(lines):
        ax = fig.add_subplot(gs[i // 2, i % 2])
        axes.append(ax)
        d = dsets[ln]
        logN2 = np.log10(d['N2'].where(d['N2'] > 0))
        pc = ax.pcolormesh(d['distance'], d['depth'], logN2,
                           cmap=cmo.tempo, vmin=vmin, vmax=vmax, shading='auto')
        cs = ax.contour(d['distance'], d['depth'], d['potential_density'],
                        levels=np.arange(24.5, 27.05, 0.5), colors='k',
                        linewidths=0.6, alpha=0.7)
        ax.clabel(cs, fmt='%.1f', fontsize=7)
        ax.set_ylim(300, 0)
        ax.set_title(U.LINE_LABEL[ln])
        if i % 2 == 0:
            ax.set_ylabel('Depth (m)')
        if i // 2 == 1:
            ax.set_xlabel('Distance offshore (km)')
    cb = fig.colorbar(pc, ax=axes, pad=0.02, fraction=0.03)
    cb.set_label('log$_{10}$ N$^2$  (s$^{-2}$)')

    # summary panel: pycnocline depth (depth of max N^2) vs distance
    axs = fig.add_subplot(gs[2, :])
    for ln in U.LINES:
        d = dsets[ln]
        n2 = d['N2'].where(d['N2'] > 0)
        # depth of max N^2 per distance (upper 250 m to avoid deep spikes)
        n2u = n2.sel(depth=slice(0, 250))
        zmax = n2u['depth'].values[n2u.fillna(-1).argmax(dim='depth').values]
        valid = np.isfinite(n2u.max(dim='depth').values)
        zmax = np.where(valid, zmax, np.nan)
        axs.plot(d['distance'], zmax, '-', color=U.LINE_COLORS[ln],
                 lw=1.8, label=U.LINE_LABEL[ln])
    axs.set_ylim(150, 0)
    axs.set_xlabel('Distance offshore (km)')
    axs.set_ylabel('Pycnocline depth (m)')
    axs.set_title('Depth of maximum stratification (N$^2$ peak, upper 250 m)')
    axs.legend(ncol=5, fontsize=8, loc='lower right')
    axs.grid(alpha=0.25)

    fig.suptitle('CUGN mean stratification (short-term climatology, 2017-2025)',
                 fontsize=13, y=0.995)
    out = os.path.join(U.FIGDIR, 'wm_stratification.png')
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    U.apply_style()
    print('wrote', fig_stratification())


if __name__ == '__main__':
    main()
