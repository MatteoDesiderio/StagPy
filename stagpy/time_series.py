"""Plots time series of temperature and heat fluxes outputs from stagyy.

Author: Stephane Labrosse with inputs from Martina Ulvrova and Adrien Morison
Date: 2015/11/27
"""
from inspect import getdoc
import numpy as np
from math import sqrt
import matplotlib.pyplot as plt
from . import conf, constants, misc
from .error import UnknownTimeVarError
from .stagyydata import StagyyData


def _plot_time_list(lovs, tseries, metas, times=None):
    """Plot requested profiles"""
    if times is None:
        times = {}
    for vfig in lovs:
        fig, axes = plt.subplots(nrows=len(vfig), sharex=True,
                                      figsize=(30, 5 * len(vfig)))
        axes = [axes] if len(vfig) == 1 else axes
        fname = ''
        for iplt, vplt in enumerate(vfig):
            ylabel = None
            for tvar in vplt:
                fname += tvar + '_'
                time = times[tvar] if tvar in times else tseries['t']
                axes[iplt].plot(time, tseries[tvar],
                                label=metas[tvar].description,
                                linewidth=conf.core.linewidth)
                lbl = metas[tvar].shortname
                if ylabel is None:
                    ylabel = lbl
                elif ylabel != lbl:
                    ylabel = ''
            if ylabel:
                axes[iplt].set_ylabel(r'${}$'.format(ylabel),
                                      fontsize=conf.core.fontsize)
            if vplt[0][:3] == 'eta':  # list of log variables
                axes[iplt].set_yscale('log')
            axes[iplt].legend(fontsize=conf.core.fontsize)
            axes[iplt].tick_params(labelsize=conf.core.fontsize)
        axes[-1].set_xlabel(r'$t$', fontsize=conf.core.fontsize)
        axes[-1].set_xlim((tseries['t'].iloc[0], tseries['t'].iloc[-1]))
        axes[-1].tick_params(labelsize=conf.core.fontsize)
        fig.savefig('time_{}.pdf'.format(fname[:-1]),
                    format='PDF', bbox_inches='tight')
        plt.close(fig)


def get_time_series(sdat, var, tstart, tend):
    """Return read or computed time series along with metadata"""
    tseries = sdat.tseries_between(tstart, tend)
    if var in tseries.columns:
        series = tseries[var]
        time = None
        if var in constants.TIME_VARS:
            meta = constants.TIME_VARS[var]
        else:
            meta = constants.Varr(None, None)
    elif var in constants.TIME_VARS_EXTRA:
        meta = constants.TIME_VARS_EXTRA[var]
        series, time = meta.description(sdat, tstart, tend)
        meta = constants.Varr(getdoc(meta.description), meta.shortname)
    else:
        raise UnknownTimeVarError(var)

    return series, time, meta


def plot_time_series(sdat, lovs):
    """Plot requested time series"""
    sovs = misc.set_of_vars(lovs)
    tseries = {}
    times = {}
    metas = {}
    for tvar in sovs:
        series, time, meta = get_time_series(
            sdat, tvar, conf.time.tstart, conf.time.tend)
        tseries[tvar] = series
        metas[tvar] = meta
        if time is not None:
            times[tvar] = time
    tseries['t'] = get_time_series(
        sdat, 't', conf.time.tstart, conf.time.tend)[0]

    _plot_time_list(lovs, tseries, metas, times)


def compstat(sdat, tstart=0., tend=None):
    """Compute statistics"""
    data = sdat.tseries_between(tstart, tend)
    time = data['t'].values

    moy = []
    rms = []
    delta_time = time[-1] - time[0]
    for col in data.columns[1:]:
        moy.append(np.trapz(data[col], x=time) / delta_time)
        rms.append(sqrt(np.trapz((data[col] - moy[-1])**2, x=time) /
                        delta_time))
    results = moy + rms
    with open('statistics.dat', 'w') as out_file:
        for item in results:
            out_file.write("%10.5e " % item)
        out_file.write("\n")


def time_cmd():
    """plot temporal series"""
    sdat = StagyyData(conf.core.path)
    if sdat.tseries is None:
        return

    lovs = misc.list_of_vars(conf.time.plot)
    if lovs:
        plot_time_series(sdat, lovs)

    if conf.time.compstat:
        compstat(sdat, conf.time.tstart, conf.time.tend)
