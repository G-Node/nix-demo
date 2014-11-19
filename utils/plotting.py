# !/usr/bin/env python
#  -*- coding: utf-8 -*-
from __future__ import print_function, division

import numpy as np
import scipy.signal as sp
import random

import nix
import matplotlib.pyplot as plt

COLORS_BLUE_AND_RED = (
    'dodgerblue', 'red'
)

COLORS_BLUE_GRADIENT = (
    "#034980", "#055DA1", "#1B70E0", "#3786ED", "#4A95F7",
    "#0C3663", "#1B4775", "#205082", "#33608F", "#51779E",
    "#23B0DB", "#29CDFF", "#57D8FF", "#8FE5FF"
)


class Plotter(object):
    def __init__(self, width=900, height=1200, dpi=90, lines=1, cols=1, facecolor="white",
                 defaultcolors=COLORS_BLUE_GRADIENT):

        assert 0 < lines < 10, "The number of lines should be between 1 and 9"
        assert 0 < cols < 10, "The number of columns should be between 1 and 9"

        self.__lines = lines
        self.__cols = cols
        self.__defaultcolors = defaultcolors

        # TODO ggplot style

        self.__figure = plt.figure(facecolor=facecolor, figsize=(width / dpi, height / dpi), dpi=90)
        self.__figure.subplots_adjust(wspace=0.3, hspace=0.3, left=0.1, right=0.9, bottom=0.05, top=0.95)

        # list of tuples each containing an axis object/None and the plot count
        self.__axis_list = ([None, 0], )
        for i in range(self.subplot_count - 1):
            self.__axis_list += ([None, 0], )

    @property
    def figure(self):
        return self.__figure

    @property
    def subplot_count(self):
        return self.__cols * self.__lines

    @property
    def axis_list(self):
        return self.__axis_list

    def save(self, name):
        self.figure.savefig(name)

    def add_plot(self, array, subplot=0, color=None, xlim=None, down_sample=None, xrange=None):
        """
        Add a new data array to the plot.

        :param array:       The data array to plot
        :param subplot:     The index of the subplot where the array should be added (starting with 0)
        :param color:       The color of the array to plot (if None the next default colors will be assigned)
        :param xlim:        Start and end of the x-axis limits.
        :param down_sample: True if the array should be downsampled
        :param xrange:      Range for the x-axis (only effective for 1d arrays with set dimension)

        :return: The axis object the array was plotted to
        """
        shape = array.shape
        nd = len(shape)

        color = self.__mk_color(color, subplot)

        if self.axis_list[subplot][0] is None:
            plot_index = self.__mk_subplot_index(subplot)
            axis = self.figure.add_subplot(*plot_index)
            axis.tick_params(direction='out')
            axis.spines['top'].set_color('none')
            axis.spines['right'].set_color('none')
            axis.xaxis.set_ticks_position('bottom')
            axis.yaxis.set_ticks_position('left')
            self.axis_list[subplot][0] = axis
        else:
            axis = self.axis_list[subplot][0]

        if nd == 1:
            self.__plot_array_1d(array, shape, subplot, color, xlim, down_sample, xrange)
        elif nd == 2:
            self.__plot_array_2d(array, shape, subplot, color, xlim, down_sample)

        self.axis_list[subplot][1] += 1

        return axis

    def __plot_array_1d(self, array, shape, subplot, color, xlim, down_sample, xrange):
        dim = array.dimensions[0]

        axis = self.axis_list[subplot][0]


        if dim.dimension_type == nix.DimensionType.Set:
            x = array[xrange or Ellipsis]  # what is xrange for
            z = np.ones_like(x) * 0.5 * axis.get_ylim()[1]
            axis.scatter(x, z, 10, color, linewidths=0, label=array.name)
            axis.set_xlabel('%s [%s]' % (array.label, array.unit))
            axis.set_ylabel(array.name)
            axis.set_yticks([])

        elif dim.dimension_type in (nix.DimensionType.Sample, nix.DimensionType.Range):
            y = array[:]
            if dim.dimension_type == nix.DimensionType.Sample:
                x_start = dim.offset or 0
                x = np.arange(0, shape[0]) * dim.sampling_interval + x_start
            else:
                x = np.array(dim.ticks)
            if down_sample is not None:
                x = sp.decimate(x, down_sample)
                y = sp.decimate(y, down_sample)
            if xlim is not None:
                x = x[np.all((x >= xlim[0], x <= xlim[1]), axis=0)]
                y = y[np.all((x >= xlim[0], x <= xlim[1]), axis=0)]
            axis.plot(x, y, color, label=array.name)
            axis.set_xlabel('%s [%s]' % (dim.label, dim.unit))
            axis.set_ylabel('%s [%s]' % (array.label, array.unit))
            axis.set_xlim([np.min(x), np.max(x)])

        else:
            raise Exception('Unsupported data')
        axis.legend()

    def __plot_array_2d(self, array, shape, subplot, color, xlim=None, down_sample=None):
        d1 = array.dimensions[0]
        d2 = array.dimensions[1]

        d1_type = d1.dimension_type
        d2_type = d2.dimension_type

        axis = self.axis_list[subplot]

        if d1_type == nix.DimensionType.Sample and d2_type == nix.DimensionType.Sample:
            z = array[:]
            x_start = d1.offset or 0
            y_start = d2.offset or 0
            x_end = x_start + shape[0] * d1.sampling_interval
            y_end = y_start + shape[1] * d2.sampling_interval

            axis.imshow(z, origin='lower', extent=[x_start, x_end, y_start, y_end])
            axis.set_xlabel('%s [%s]' % (d1.label, d1.unit))
            axis.set_ylabel('%s [%s]' % (d2.label, d2.unit))
            axis.set_title(array.name)
            bar = plt.colorbar()
            bar.label('%s [%s]' % (array.label, array.unit))

        elif d1_type == nix.DimensionType.Set and d2_type == nix.DimensionType.Sample:
            x_start = d2.offset or 0
            x_one = x_start + np.arange(0, shape[1]) * d2.sampling_interval
            x = np.tile(x_one.reshape(shape[1], 1), shape[0])
            y = array[:]
            axis.plot(x, y.T, color=color)
            axis.set_title(array.name)
            axis.set_xlabel('%s [%s]' % (d2.label, d2.unit))
            axis.set_ylabel('%s [%s]' % (array.label, array.unit))

            if d1.labels is not None:
                axis.legend(d1.labels)
        else:
            raise Exception('Unsupported data')
        axis.legend()

    def __mk_subplot_index(self, subplot):
        return self.__lines, self.__cols, subplot + 1

    def __mk_color(self, color, subplot):
        if color is None:
            color_all = self.__defaultcolors
            color_count = len(color_all)
            count = self.axis_list[subplot][1]
            color = color_all[count if count < color_count else color_count - 1]

        if color == "random":
            color = "#%02x%02x%02x" % (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

        return color