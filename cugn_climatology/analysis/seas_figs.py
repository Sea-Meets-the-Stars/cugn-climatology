"""Figures characterizing the CUGN 2026-beta seasonal (annual) cycle.

Run from this directory:  conda run -n ocean14 python seas_figs.py
Writes context/figs/seas_*.png.

Uses harmonic fits (annual + semiannual) from seas_harmonic.py applied to the
`annual_cycle` (anomaly-form) depth files.
"""
import os
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cmocean

import seas_harmonic as sh

FIGDIR = sh.FIGDIR
os.makedirs(FIGDIR, exist_ok=True)

ST_LINES = ['56', '66', '80', '90', 'al']
LT_LINES = ['66', '80', '90']
LINE_COLORS = {'56': '#1b9e77', '66': '#d95f02', '80': '#7570b3',
               '90': '#e7298a', 'al': '#66a61e'}

VAR_INFO = {
    'temperature':   ('Temperature', r'$^\circ$C',          cmocean.cm.thermal),
    'salinity':      ('Salinity',    'PSS-78',               cmocean.cm.haline),
    'chlorophyll_a': ('Chlorophyll-a', r'mg m$^{-3}$',       cmocean.cm.algae),
    'doxy':          ('Dissolved O$_2$', r'$\mu$mol kg$^{-1}$', cmocean.cm.oxy),
}


def fit_line(group, line, var):
    ds, doy = sh.load_annual_cycle(group, 'depth', line)
    if var not in ds:
        return None
    res = sh.harmonic_fit(ds[var].values, doy)
    res['depth'] = ds['depth'].values
    res['distance'] = ds['distance'].values
    return res


# ---------------------------------------------------------------------------
# Figure 1: annual amplitude vs depth (cross-shore averaged), st lines
# ---------------------------------------------------------------------------
def fig_amp_depth_profiles():
    variables = ['temperature', 'salinity', 'chlorophyll_a', 'doxy']
    fig, axes = plt.subplots(1, 4, figsize=(14, 6), sharey=True)
    for ax, var in zip(axes, variables):
        name, units, _ = VAR_INFO[var]
        for line in ST_LINES:
            r = fit_line('st', line, var)
            if r is None:
                continue
            prof = np.nanmean(r['amp1'], axis=1)
            ax.plot(prof, r['depth'], color=LINE_COLORS[line], lw=2,
                    label=f'Line {line}')
        # e-folding annotation from line 90 (or 80 for context)
        r90 = fit_line('st', '90', var)
        if r90 is not None:
            prof90 = np.nanmean(r90['amp1'], axis=1)
            m = r90['depth'] <= 150
            H, A0 = sh.efolding_depth(r90['depth'][m], prof90[m])
            if np.isfinite(H):
                ax.text(0.95, 0.02, f'L90 H$\\approx${H:.0f} m\n(10-150 m)',
                        transform=ax.transAxes, ha='right', va='bottom', fontsize=8,
                        bbox=dict(boxstyle='round', fc='white', alpha=0.7))
        ax.set_title(f'{name}')
        ax.set_xlabel(f'Annual amplitude ({units})')
        ax.grid(alpha=0.3)
        ax.set_xlim(left=0)
    axes[0].set_ylabel('Depth (m)')
    axes[0].set_ylim(500, 0)
    axes[0].legend(fontsize=8, loc='center right')
    fig.suptitle('Seasonal (annual-harmonic) amplitude vs depth — cross-shore averaged, short-term (2017-2025)',
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(FIGDIR, 'seas_amp_depth_profiles.png')
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print('wrote', out)


# ---------------------------------------------------------------------------
# Figure 2: cross-shore x depth amplitude sections (st line 90)
# ---------------------------------------------------------------------------
def fig_amp_sections(line='90'):
    variables = ['temperature', 'salinity', 'chlorophyll_a', 'doxy']
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for ax, var in zip(axes.ravel(), variables):
        name, units, cmap = VAR_INFO[var]
        r = fit_line('st', line, var)
        dist, depth = r['distance'], r['depth']
        amp = r['amp1']
        pm = ax.pcolormesh(dist, depth, amp, cmap=cmap, shading='auto')
        cb = fig.colorbar(pm, ax=ax)
        cb.set_label(f'annual amp ({units})')
        # overlay 25/50/75% of local-column-max contour? use amplitude contours
        ax.set_title(f'{name} — annual amplitude')
        ax.set_ylim(500, 0)
        ax.set_xlabel('Cross-shore distance (km)')
        ax.set_ylabel('Depth (m)')
    fig.suptitle(f'Seasonal amplitude cross-sections — st Line {line} (offshore = larger distance)',
                 fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = os.path.join(FIGDIR, f'seas_amp_sections_st{line}.png')
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print('wrote', out)


# ---------------------------------------------------------------------------
# Figure 3: phase (month of max) - depth structure for T and doxy (st 90),
#           masked where amplitude is negligible.
# ---------------------------------------------------------------------------
def fig_phase_sections(line='90'):
    variables = ['temperature', 'doxy']
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, var in zip(axes, variables):
        name, units, _ = VAR_INFO[var]
        r = fit_line('st', line, var)
        dist, depth = r['distance'], r['depth']
        ph = r['phase_doy'].copy()
        amp = r['amp1']
        # mask where seasonal signal is weak (< 10% of the column max amplitude)
        thr = 0.1 * np.nanmax(amp)
        ph[amp < thr] = np.nan
        # convert doy -> month fraction (1-13) for a cyclic colormap
        month = ph / 365.0 * 12.0
        pm = ax.pcolormesh(dist, depth, month, cmap=cmocean.cm.phase,
                           vmin=0, vmax=12, shading='auto')
        cb = fig.colorbar(pm, ax=ax, ticks=np.arange(0, 13, 2))
        cb.set_label('month of maximum')
        cb.ax.set_yticklabels(['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov', 'Jan'])
        ax.set_title(f'{name} — phase (month of annual max)')
        ax.set_ylim(400, 0)
        ax.set_xlabel('Cross-shore distance (km)')
        ax.set_ylabel('Depth (m)')
    fig.suptitle(f'Seasonal phase structure — st Line {line} '
                 '(weak-amplitude regions masked)', fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = os.path.join(FIGDIR, f'seas_phase_sections_st{line}.png')
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print('wrote', out)


# ---------------------------------------------------------------------------
# Figure 4: near-surface (10 m) annual amplitude vs cross-shore distance,
#           all st lines, per variable.
# ---------------------------------------------------------------------------
def fig_surface_crossshore():
    variables = ['temperature', 'salinity', 'chlorophyll_a', 'doxy']
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.5))
    for ax, var in zip(axes, variables):
        name, units, _ = VAR_INFO[var]
        for line in ST_LINES:
            r = fit_line('st', line, var)
            if r is None:
                continue
            iz = int(np.argmin(np.abs(r['depth'] - 10.0)))
            ax.plot(r['distance'], r['amp1'][iz, :], color=LINE_COLORS[line],
                    lw=2, label=f'Line {line}')
        ax.set_title(name)
        ax.set_xlabel('Cross-shore distance (km)')
        ax.set_ylabel(f'10 m annual amp ({units})')
        ax.grid(alpha=0.3)
        ax.set_ylim(bottom=0)
    axes[0].legend(fontsize=8)
    fig.suptitle('Near-surface (10 m) seasonal amplitude vs cross-shore distance — short-term lines',
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = os.path.join(FIGDIR, 'seas_surface_crossshore.png')
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print('wrote', out)


# ---------------------------------------------------------------------------
# Figure 5: lt vs st comparison of the temperature seasonal cycle:
#   depth profile of amplitude, and phase-with-depth (downward propagation).
# ---------------------------------------------------------------------------
def fig_lt_st_and_phasedepth():
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    # left: T amplitude vs depth, lt vs st, common lines 66/80/90
    ax = axes[0]
    for line in LT_LINES:
        for group, ls in [('lt', '--'), ('st', '-')]:
            r = fit_line(group, line, 'temperature')
            prof = np.nanmean(r['amp1'], axis=1)
            ax.plot(prof, r['depth'], ls, color=LINE_COLORS[line], lw=2,
                    label=f'{group} {line}')
    ax.set_xlabel(r'T annual amplitude ($^\circ$C)')
    ax.set_ylabel('Depth (m)')
    ax.set_ylim(300, 0)
    ax.set_xlim(left=0)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, ncol=2)
    ax.set_title('T seasonal amplitude: long-term (--) vs short-term (—)')

    # right: T phase (month of max) vs depth, cross-shore averaged, st lines
    ax = axes[1]
    for line in ST_LINES:
        r = fit_line('st', line, 'temperature')
        amp = r['amp1']
        ph = r['phase_doy'].copy()
        thr = 0.1 * np.nanmax(amp)
        ph[amp < thr] = np.nan
        # circular mean across distance
        ang = ph / 365.0 * 2 * np.pi
        mean_ang = np.arctan2(np.nanmean(np.sin(ang), axis=1),
                              np.nanmean(np.cos(ang), axis=1))
        month = (mean_ang % (2 * np.pi)) / (2 * np.pi) * 12.0
        # break the plotted line where the phase wraps >4 months between
        # adjacent depths (the physical surface->deep phase reversal), so the
        # cyclic axis does not draw a long horizontal jump across the panel.
        mplot = month.copy()
        jump = np.abs(np.diff(mplot)) > 4.0
        mplot[1:][jump] = np.nan
        ax.plot(mplot, r['depth'], color=LINE_COLORS[line], lw=2, label=f'Line {line}')
    ax.set_xlabel('T month of maximum')
    ax.set_xlim(0, 12)
    ax.set_xticks(range(0, 13, 2))
    ax.set_xticklabels(['Jan', 'Mar', 'May', 'Jul', 'Sep', 'Nov', 'Jan'])
    ax.set_ylim(300, 0)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title('T phase vs depth (downward propagation, st)')
    fig.suptitle('Temperature seasonal cycle: amplitude baselines and phase-depth structure',
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = os.path.join(FIGDIR, 'seas_T_amp_phase_depth.png')
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print('wrote', out)


if __name__ == '__main__':
    fig_amp_depth_profiles()
    fig_amp_sections('90')
    fig_phase_sections('90')
    fig_surface_crossshore()
    fig_lt_st_and_phasedepth()
    print('done')
