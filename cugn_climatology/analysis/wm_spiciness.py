"""Spiciness / density-compensation structure of the CUGN 2026-beta mean
fields (short-term group).

Spiciness (TEOS-10 spiciness0) measures the along-isopycnal T-S signature:
warm+salty water is "spicy", cold+fresh is "minty". Variations of spiciness on
a density surface are density-compensated (they do not change the density) and
trace distinct source water masses.

Produces:
    wm_spiciness_section.png   Cross-sections of spiciness (depth coords) for
                               the four cross-shore lines, with sigma-theta
                               contours. Shows the spicy surface / minty
                               subsurface split and the upwelling signature.
    wm_isopycnal_spice.png     Spiciness ON isopycnals (from the sigma-coord
                               mean files): (a) spice vs distance for selected
                               density surfaces, all lines; (b) mean spice
                               profile vs potential density by line (latitude
                               ordering of water masses).

Run:
    python -m cugn_climatology.analysis.wm_spiciness
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cmocean.cm as cmo
import gsw

from cugn_climatology.analysis import wm_utils as U


def _load_depth(line):
    return U.add_teos10(U.open_ds('st', 'mean', 'depth', line))


def _spice_on_sigma(line):
    """Return the sigma-coord mean ds with SA, CT, spice added.

    Pressure is derived from the stored mean `depth` of each isopycnal.
    """
    ds = U.open_ds('st', 'mean', 'sigma', line)
    lat = ds['latitude']; lon = ds['longitude']
    p = gsw.p_from_z(-ds['depth'], float(lat.mean()))     # (potential_density, distance)
    SA = gsw.SA_from_SP(ds['salinity'], p, lon, lat)
    CT = gsw.CT_from_t(SA, ds['temperature'], p)
    spice = gsw.spiciness0(SA, CT)
    return ds.assign(SA=SA, CT=CT, spice=spice)


def fig_spiciness_section():
    lines = U.XSHORE
    dsets = {ln: _load_depth(ln) for ln in lines}
    sp_all = np.concatenate([d['spice'].values.ravel() for d in dsets.values()])
    sp_all = sp_all[np.isfinite(sp_all)]
    vmin, vmax = np.percentile(sp_all, [2, 98])

    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=False, sharey=True)
    axes = axes.ravel()
    for i, ln in enumerate(lines):
        ax = axes[i]
        d = dsets[ln]
        pc = ax.pcolormesh(d['distance'], d['depth'], d['spice'],
                           cmap=cmo.balance, vmin=vmin, vmax=vmax, shading='auto')
        cs = ax.contour(d['distance'], d['depth'], d['potential_density'],
                        levels=np.arange(24.5, 27.05, 0.5), colors='k',
                        linewidths=0.6, alpha=0.6)
        ax.clabel(cs, fmt='%.1f', fontsize=7)
        ax.set_ylim(300, 0)
        ax.set_title(U.LINE_LABEL[ln])
        if i % 2 == 0:
            ax.set_ylabel('Depth (m)')
        if i // 2 == 1:
            ax.set_xlabel('Distance offshore (km)')
    cb = fig.colorbar(pc, ax=axes, pad=0.02, fraction=0.03)
    cb.set_label('Spiciness  (kg m$^{-3}$)')
    fig.suptitle('CUGN mean spiciness (short-term climatology, 2017-2025)',
                 fontsize=13, y=0.98)
    out = os.path.join(U.FIGDIR, 'wm_spiciness_section.png')
    fig.savefig(out)
    plt.close(fig)
    return out


def fig_isopycnal_spice():
    dsets = {ln: _spice_on_sigma(ln) for ln in U.LINES}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))

    # (a) spice vs distance for selected density surfaces, all lines
    ax = axes[0]
    surfaces = [25.0, 25.5, 26.0, 26.5]
    styles = ['-', '--', ':', '-.']
    for ln in U.LINES:
        d = dsets[ln]
        for sig, st in zip(surfaces, styles):
            sp = d['spice'].sel(potential_density=sig)
            ax.plot(d['distance'], sp, st, color=U.LINE_COLORS[ln], lw=1.4)
    ax.set_xlabel('Distance offshore (km)')
    ax.set_ylabel('Spiciness on isopycnal  (kg m$^{-3}$)')
    ax.set_title('(a) Along-isopycnal spiciness vs distance')
    ax.grid(alpha=0.25)
    # two legends: colour = line, linestyle = density surface
    from matplotlib.lines import Line2D
    lh = [Line2D([0], [0], color=U.LINE_COLORS[ln], lw=2, label=U.LINE_LABEL[ln])
          for ln in U.LINES]
    sh = [Line2D([0], [0], color='0.3', lw=1.4, ls=st,
                 label=f'$\\sigma_\\theta$={sig:.1f}')
          for sig, st in zip(surfaces, styles)]
    leg1 = ax.legend(handles=lh, loc='upper right', fontsize=8, framealpha=0.9)
    ax.add_artist(leg1)
    ax.legend(handles=sh, loc='lower left', fontsize=8, framealpha=0.9)

    # (b) mean spice profile vs potential density by line
    ax = axes[1]
    for ln in U.LINES:
        d = dsets[ln]
        prof = d['spice'].mean(dim='distance', skipna=True)
        ax.plot(prof, d['potential_density'], '-o', ms=3,
                color=U.LINE_COLORS[ln], lw=1.6, label=U.LINE_LABEL[ln])
    ax.set_ylim(27.05, 24.95)
    ax.set_xlabel('Line-mean spiciness  (kg m$^{-3}$)')
    ax.set_ylabel('Potential density  $\\sigma_\\theta$  (kg m$^{-3}$)')
    ax.set_title('(b) Line-mean spiciness vs density (water-mass fingerprint)')
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc='upper left')

    fig.suptitle('CUGN along-isopycnal spiciness (short-term climatology, 2017-2025)',
                 fontsize=13, y=1.0)
    fig.tight_layout()
    out = os.path.join(U.FIGDIR, 'wm_isopycnal_spice.png')
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    U.apply_style()
    for o in (fig_spiciness_section(), fig_isopycnal_spice()):
        print('wrote', o)


if __name__ == '__main__':
    main()
