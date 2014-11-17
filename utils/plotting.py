#!/usr/bin/env python
#  -*- coding: utf-8 -*-
from __future__ import print_function, division

import nix
import numpy as np
import scipy.signal as sp
import matplotlib as mpl
import matplotlib.pyplot as plt

class Plotter(object):
    def __init__(self, figure=None, try_ggplot_style=True):
        self._post_plot_hook = None
        
        if try_ggplot_style:
            self._setup_ggplot()
        if figure is None:
            self.fig = plt.figure(facecolor='white')
            plt.hold('on')
        else:
            self.fig = figure
        self._n_plots = 0
        self._x_range = None
        self.axis = None

    def _setup_ggplot(self):
        try:
            from ggplot import theme_bw
            t = theme_bw()
            for k, v in t.get_rcParams().iteritems():
                mpl.rcParams[k] = v

            def plot_post_hook():
                for ax in self.figure.axes:
                    t.post_plot_callback(ax)
            self._post_plot_hook = plot_post_hook
        except ImportError:
            pass
        except AttributeError:
            pass

    @property
    def figure(self):
        return self.fig

    @property
    def xrange(self):
        return self._x_range

    @xrange.setter
    def xrange(self, value):
        self._x_range = value

    def add_plot(self, array, axis=None, xlim=None, down_sample=None):
        shape = array.shape
        nd = len(shape)
        if axis is None and self.axis is None:
            self.axis = self.fig.add_subplot(111)
            self.axis.tick_params(direction='out')
            self.axis.spines['top'].set_color('none')
            self.axis.spines['right'].set_color('none')
            self.axis.xaxis.set_ticks_position('bottom')
            self.axis.yaxis.set_ticks_position('left')
        elif axis is not None:
            self.axis = axis
        
        if nd == 1:
            self._plot_array_1d(array, shape, xlim=xlim, down_sample=down_sample)
        elif nd == 2:
            self._plot_array_2d(array, shape, xlim=xlim, down_sample=down_sample)

        self._n_plots += 1

        if self._post_plot_hook is not None:
            self._post_plot_hook()
        return self.axis

    def _plot_array_1d(self, array, shape, xlim=None, down_sample=None):
        dim = array.dimensions[0]
        
        if dim.dimension_type == nix.DimensionType.Set:
            x = array[self.xrange or Ellipsis]
            z = np.ones_like(x) * 0.5 * self.axis.get_ylim()[1]
            #TODO: the color logic below is stupid
            self.axis.scatter(x, z, 10, 'dodgerblue' if self._n_plots == 0 else 'red',
                              linewidths=0, label='%s [%s]' % (array.name, array.type))
            self.axis.set_xlabel('%s [%s]' % (array.label, array.unit))
            self.axis.set_ylabel(array.name)
            self.axis.set_yticks([])

        elif dim.dimension_type == nix.DimensionType.Sample:
            y = array[:]
            x_start = dim.offset or 0
            x = np.arange(0, shape[0]) * dim.sampling_interval + x_start
            if down_sample is not None:
                x = sp.decimate(x, down_sample)
                y = sp.decimate(y, down_sample)
            if xlim is not None:
                x = x[np.all((x>=xlim[0],x<=xlim[1]),axis=0)]
                y = y[np.all((x>=xlim[0],x<=xlim[1]),axis=0)]
            self.axis.plot(x, y, 'dodgerblue', label='%s [%s]' % (array.name, array.type))
            self.axis.set_xlabel('%s [%s]' % (dim.label, dim.unit))
            self.axis.set_ylabel('%s [%s]' % (array.label, array.unit))
            self.axis.set_xlim([np.min(x), np.max(x)])
        else:
            raise Exception('Unsupported data')
        self.axis.legend()

    def _plot_array_2d(self, array, shape, xlim=None, down_sample=None):
        d1 = array.dimensions[0]
        d2 = array.dimensions[1]

        d1_type = d1.dimension_type
        d2_type = d2.dimension_type
        
        if d1_type == nix.DimensionType.Sample and d2_type == nix.DimensionType.Sample:
            z = array[:]
            x_start = d1.offset or 0
            y_start = d2.offset or 0
            x_end = x_start + shape[0] * d1.sampling_interval
            y_end = y_start + shape[1] * d2.sampling_interval

            self.axis.imshow(z, origin='lower', extent=[x_start, x_end, y_start, y_end])
            self.axis.set_xlabel('%s [%s]' % (d1.label, d1.unit))
            self.axis.set_ylabel('%s [%s]' % (d2.label, d2.unit))
            self.axis.set_title('%s [%s]' % (array.name, array.type))
            bar = plt.colorbar()
            bar.label('%s [%s]' % (array.label, array.unit))

        elif d1_type == nix.DimensionType.Set and d2_type == nix.DimensionType.Sample:
            x_start = d2.offset or 0
            x_one = x_start + np.arange(0, shape[1]) * d2.sampling_interval
            x = np.tile(x_one.reshape(shape[1], 1), shape[0])
            y = array[:]
            self.axis.plot(x, y.T, color='dodgerblue')
            self.axis.set_title('%s [%s]' % (array.name, array.type))
            self.axis.set_xlabel('%s [%s]' % (d2.label, d2.unit))
            self.axis.set_ylabel('%s [%s]' % (array.label, array.unit))

            if d1.labels is not None:
                self.axis.legend(d1.labels)
        else:
            raise Exception('Unsupported data')
        self.axis.legend()

    def save(self, filename, width=None, height=None, units='cm', **kwargs):
        # units conversion taken from ggsave
        if units not in ["in", "cm", "mm"]:
            raise Exception("units not 'in', 'cm', or 'mm'")
        to_inch = {"in": lambda x: x, "cm": lambda x: x / 2.54, "mm": lambda x: x * 2.54 * 10}

        w_old, h_old = self.figure.get_size_inches()
        w = to_inch[units](width) if width is not None else w_old
        h = to_inch[units](height) if height is not None else h_old

        self.figure.set_size_inches(w, h)
        self.figure.savefig(filename, **kwargs)
