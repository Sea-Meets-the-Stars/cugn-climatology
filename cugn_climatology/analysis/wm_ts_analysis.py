"""Mean T-S structure of the CUGN 2026-beta climatology (short-term group).

Produces:
    wm_ts_diagram.png   Conservative-Temperature / Absolute-Salinity diagram of
                        the mean fields: (a) coloured by section line,
                        (b) all lines pooled, coloured by cross-shore distance.
    wm_ts_by_line.png   One T-S panel per line, coloured by cross-shore
                        distance, to show the inshore->offshore evolution of
                        water masses on each section.

Uses TEOS-10 (SA, CT, spiciness). Run:

    python -m cugn_climatology.analysis.wm_ts_analysis
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from cugn_climatology.analysis import wm_utils as U


def _load(line):
    return U.add_teos10(U.open_ds('st', 'mean', 'depth', line))


def fig_ts_diagram():
    dsets = {ln: _load(ln) for ln in U.LINES}
    # global S/T limits (SA, CT)
    SA_all = np.concatenate([d['SA'].values.ravel() for d in dsets.values()])
    CT_all = np.concatenate([d['CT'].values.ravel() for d in dsets.values()])
    ok = np.isfinite(SA_all) & np.isfinite(CT_all)
    slim = (np.floor(np.nanpercentile(SA_all[ok], 0.1) * 10) / 10,
            np.ceil(np.nanpercentile(SA_all[ok], 99.9) * 10) / 10)
    tlim = (np.floor(np.nanmin(CT_all[ok])), np.ceil(np.nanmax(CT_all[ok])))

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))

    # (a) coloured by line
    ax = axes[0]
    U.ts_density_grid(ax, slim, tlim)
    for ln in U.LINES:
        d = dsets[ln]
        ax.scatter(d['SA'].values.ravel(), d['CT'].values.ravel(),
                   s=6, c=U.LINE_COLORS[ln], alpha=0.45, edgecolors='none',
                   label=U.LINE_LABEL[ln], zorder=3)
    handles = [Line2D([0], [0], marker='o', ls='', color=U.LINE_COLORS[ln],
                      label=U.LINE_LABEL[ln]) for ln in U.LINES]
    ax.legend(handles=handles, loc='upper left', framealpha=0.9)
    ax.set_xlim(slim); ax.set_ylim(tlim)
    ax.set_xlabel('Absolute Salinity  S$_A$  (g kg$^{-1}$)')
    ax.set_ylabel('Conservative Temperature  $\\Theta$  ($^\\circ$C)')
    ax.set_title('(a) Mean T-S by section line')
    _annotate_masses(ax)

    # (b) pooled, coloured by cross-shore distance
    ax = axes[1]
    U.ts_density_grid(ax, slim, tlim)
    SA_p, CT_p, dist_p = [], [], []
    for ln in U.LINES:
        d = dsets[ln]
        dist2d = d['distance'].broadcast_like(d['SA'])
        SA_p.append(d['SA'].values.ravel())
        CT_p.append(d['CT'].values.ravel())
        dist_p.append(dist2d.values.ravel())
    SA_p = np.concatenate(SA_p); CT_p = np.concatenate(CT_p)
    dist_p = np.concatenate(dist_p)
    sc = ax.scatter(SA_p, CT_p, c=dist_p, s=6, cmap='viridis',
                    alpha=0.55, edgecolors='none', zorder=3)
    cb = fig.colorbar(sc, ax=ax, pad=0.02)
    cb.set_label('Cross-shore distance (km, 0 = inshore)')
    ax.set_xlim(slim); ax.set_ylim(tlim)
    ax.set_xlabel('Absolute Salinity  S$_A$  (g kg$^{-1}$)')
    ax.set_ylabel('Conservative Temperature  $\\Theta$  ($^\\circ$C)')
    ax.set_title('(b) All lines pooled, coloured by distance offshore')

    fig.suptitle('CUGN mean water-mass structure (short-term climatology, 2017-2025)',
                 fontsize=13, y=1.00)
    fig.tight_layout()
    out = os.path.join(U.FIGDIR, 'wm_ts_diagram.png')
    fig.savefig(out)
    plt.close(fig)
    return out


def _annotate_masses(ax):
    ax.annotate('warm, fresh\nsurface layer\n(spicy)', xy=(33.30, 16.8),
                fontsize=8, ha='center', color='0.15',
                bbox=dict(boxstyle='round', fc='white', ec='0.6', alpha=0.85))
    ax.annotate('cold, salty\nthermocline / deep\n($\\sigma_\\theta\\approx$26.5-27)',
                xy=(34.28, 7.6), fontsize=8, ha='center', color='0.15',
                bbox=dict(boxstyle='round', fc='white', ec='0.6', alpha=0.85))


def fig_ts_by_line():
    lines = U.LINES
    n = len(lines)
    ncol = 3
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(13, 8), sharex=True, sharey=True)
    axes = axes.ravel()
    dsets = {ln: _load(ln) for ln in lines}
    SA_all = np.concatenate([d['SA'].values.ravel() for d in dsets.values()])
    CT_all = np.concatenate([d['CT'].values.ravel() for d in dsets.values()])
    ok = np.isfinite(SA_all) & np.isfinite(CT_all)
    slim = (np.floor(np.nanpercentile(SA_all[ok], 0.1) * 10) / 10,
            np.ceil(np.nanpercentile(SA_all[ok], 99.9) * 10) / 10)
    tlim = (np.floor(np.nanmin(CT_all[ok])), np.ceil(np.nanmax(CT_all[ok])))

    for i, ln in enumerate(lines):
        ax = axes[i]
        d = dsets[ln]
        U.ts_density_grid(ax, slim, tlim, color='0.75')
        dist2d = d['distance'].broadcast_like(d['SA'])
        sc = ax.scatter(d['SA'].values.ravel(), d['CT'].values.ravel(),
                        c=dist2d.values.ravel(), s=8, cmap='viridis',
                        vmin=0, vmax=530, alpha=0.7, edgecolors='none', zorder=3)
        ax.set_title(U.LINE_LABEL[ln])
        ax.set_xlim(slim); ax.set_ylim(tlim)
    for i in range(n, len(axes)):
        axes[i].axis('off')
    # shared colorbar
    cb = fig.colorbar(sc, ax=axes, pad=0.02, fraction=0.03)
    cb.set_label('Cross-shore distance (km, 0 = inshore)')
    for ax in axes[::ncol]:
        ax.set_ylabel('$\\Theta$ ($^\\circ$C)')
    for ax in axes[-ncol:]:
        ax.set_xlabel('S$_A$ (g kg$^{-1}$)')
    fig.suptitle('Mean T-S by line, coloured by distance offshore (short-term climatology)',
                 fontsize=13)
    out = os.path.join(U.FIGDIR, 'wm_ts_by_line.png')
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    U.apply_style()
    outs = [fig_ts_diagram(), fig_ts_by_line()]
    for o in outs:
        print('wrote', o)


if __name__ == '__main__':
    main()
