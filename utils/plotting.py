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
    """
    Plotter class for nix data arrays.
    """

    def __init__(self, width=800, height=600, dpi=90, lines=1, cols=1, facecolor="white",
                 defaultcolors=COLORS_BLUE_GRADIENT):
        """


        :param width:       Width of the image in pixels
        :param height:      Height of the image in pixels
        :param dpi:         DPI of the image (default 90)
        :param lines:       Number of vertical subplots
        :param cols:        Number of horizontal subplots
        :param facecolor:   The background color of the plot
        :param defaultcolors: Defaultcolors that are assigned to lines in each subplot.
        """

        self.__width = width
        self.__height = height
        self.__dpi = dpi
        self.__lines = lines
        self.__cols = cols
        self.__facecolor = facecolor
        self.__defaultcolors = defaultcolors

        self.__subplot_data = tuple()
        for i in range(self.subplot_count):
            self.__subplot_data += ([], )

        self.__last_figure = None

    # properties

    @property
    def subplot_count(self):
        return self.__cols * self.__lines

    @property
    def subplot_data(self):
        return self.__subplot_data

    @property
    def defaultcolors(self):
        return self.__defaultcolors

    @property
    def last_figure(self):
        assert self.__last_figure is not None, "No figure available (method plot has to be called at least once)"
        return self.__last_figure

    # methods

    def save(self, name):
        """
        Saves the last figure to the specified location.

        :param name:    The name of the figure file
        """
        self.last_figure.savefig(name)

    def add(self, array, subplot=0, color=None, xlim=None, downsample=None, labels=None):
        """
        Add a new data array to the plot

        :param array:       The data array to plot
        :param subplot:     The index of the subplot where the array should be added (starting with 0)
        :param color:       The color of the array to plot (if None the next default colors will be assigned)
        :param xlim:        Start and end of the x-axis limits.
        :param downsample:  True if the array should be sampled down
        :param labels:      Data array with labels that should be added to each data point of the array to plot
        """
        color = self.__mk_color(color, subplot)
        pdata = PlottingData(array, color, subplot, xlim, downsample, labels)
        self.subplot_data[subplot].append(pdata)

    def plot(self, width=None, height=None, dpi=None, lines=None, cols=None, facecolor=None):
        """
        Plots all data arrays added to the plotter.

        :param width:       Width of the image in pixels
        :param height:      Height of the image in pixels
        :param dpi:         DPI of the image (default 90)
        :param lines:       Number of vertical subplots
        :param cols:        Number of horizontal subplots
        :param facecolor:   The background color of the plot
        """
        # defaults
        width = width or self.__width
        height = height or self.__height
        dpi = dpi or self.__dpi
        lines = lines or self.__lines
        cols = cols or self.__cols
        facecolor = facecolor or self.__facecolor

        # plot
        figure, axis_all = plot_make_figure(width, height, dpi, cols, lines, facecolor)

        for subplot, pdata_list in enumerate(self.subplot_data):
            axis = axis_all[subplot]
            pdata_list.sort()

            event_like = Plotter.__count_event_like(pdata_list)
            signal_like = Plotter.__count_signal_like(pdata_list)

            for i, pdata in enumerate(pdata_list):
                d1type = pdata.array.dimensions[0].dimension_type
                shape = pdata.array.shape
                nd = len(shape)

                if nd == 1:
                    if d1type == nix.DimensionType.Set:
                        second_y = signal_like > 0
                        hint = (i + 1.0) / (event_like + 1.0) if event_like > 0 else None
                        plot_array_1d_set(pdata.array, axis, color=pdata.color, xlim=pdata.xlim, labels=pdata.labels,
                                          second_y=second_y, hint=hint)
                    else:
                        plot_array_1d(pdata.array, axis, color=pdata.color, xlim=pdata.xlim,
                                      downsample=pdata.downsample)
                elif nd == 2:
                    if d1type == nix.DimensionType.Set:
                        plot_array_2d_set(pdata.array, axis, color=pdata.color, xlim=pdata.xlim,
                                          downsample=pdata.downsample)
                    else:
                        plot_array_2d(pdata.array, axis, color=pdata.color, xlim=pdata.xlim,
                                      downsample=pdata.downsample)
                else:
                    raise Exception('Unsupported data')

            axis.legend()

        self.__last_figure = figure

    # private methods

    def __mk_color(self, color, subplot):
        """
        If color is None, select one from the defaults or create a random color.
        """
        if color is None:
            color_count = len(self.defaultcolors)
            count = len(self.subplot_data[subplot])
            color = self.defaultcolors[count if count < color_count else color_count - 1]

        if color == "random":
            color = "#%02x%02x%02x" % (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

        return color

    @staticmethod
    def __count_signal_like(pdata_list):
        sig_types = (nix.DimensionType.Range, nix.DimensionType.Sample)
        count = 0

        for pdata in pdata_list:
            dims = pdata.array.dimensions
            nd = len(dims)

            if nd == 1 and dims[0].dimension_type in sig_types:
                count += 1
            elif nd == 2 and dims[0].dimension_type == nix.DimensionType.Set and dims[1].dimension_type in sig_types:
                count += 1

        return count

    @staticmethod
    def __count_image_like(pdata_list):
        sig_types = (nix.DimensionType.Range, nix.DimensionType.Sample)
        count = 0

        for pdata in pdata_list:
            dims = pdata.array.dimensions
            nd = len(dims)

            if nd == 2 and dims[0].dimension_type in sig_types and dims[1].dimension_type in sig_types:
                count += 1

        return count

    @staticmethod
    def __count_event_like(pdata_list):
        count = 0

        for pdata in pdata_list:
            dims = pdata.array.dimensions
            nd = len(dims)

            if dims[0].dimension_type == nix.DimensionType.Set:
                count += 1

        return count


class PlottingData(object):

    def __init__(self, array, color, subplot=0, xlim=None, downsample=False, labels=None):
        self.array = array
        self.dimensions = array.dimensions
        self.shape = array.shape
        self.rank = len(array.shape)
        self.color = color
        self.subplot = subplot
        self.xlim = xlim
        self.downsample = downsample
        self.labels = labels

    def __cmp__(self, other):
        weights = lambda dims: [(1 if d.dimension_type == nix.DimensionType.Sample else 0) for d in dims]
        return cmp(weights(self.array.dimensions), weights(other.array.dimensions))

    def __lt__(self, other):
        return self.__cmp__(other) < 0


def plot_make_figure(width, height, dpi, cols, lines, facecolor):
    axis_all = []
    figure = plt.figure(facecolor=facecolor, figsize=(width / dpi, height / dpi), dpi=90)
    figure.subplots_adjust(wspace=0.3, hspace=0.3, left=0.1, right=0.9, bottom=0.05, top=0.95)

    for subplot in range(cols * lines):

        axis = figure.add_subplot(lines, cols, subplot+1)
        axis.tick_params(direction='out')
        axis.spines['top'].set_color('none')
        axis.spines['right'].set_color('none')
        axis.xaxis.set_ticks_position('bottom')
        axis.yaxis.set_ticks_position('left')

        axis_all.append(axis)

    return figure, axis_all


def plot_array_1d(array, axis, color=None, xlim=None, downsample=None, hint=None, labels=None):
    dim = array.dimensions[0]

    assert dim.dimension_type in (nix.DimensionType.Sample, nix.DimensionType.Range), "Unsupported data"

    y = array[:]
    if dim.dimension_type == nix.DimensionType.Sample:
        x_start = dim.offset or 0
        x = np.arange(0, array.shape[0]) * dim.sampling_interval + x_start
    else:
        x = np.array(dim.ticks)
    
    if downsample is not None:
        x = sp.decimate(x, downsample)
        y = sp.decimate(y, downsample)
    if xlim is not None:
        y = y[(x >= xlim[0]) & (x <= xlim[1])]
        x = x[(x >= xlim[0]) & (x <= xlim[1])]
       
    axis.plot(x, y, color, label=array.name)
    axis.set_xlabel('%s [%s]' % (dim.label, dim.unit))
    axis.set_ylabel('%s [%s]' % (array.label, array.unit))
    axis.set_xlim([np.min(x), np.max(x)])


def plot_array_1d_set(array, axis, color=None, xlim=None, hint=None, labels=None, second_y=False):
    dim = array.dimensions[0]

    assert dim.dimension_type == nix.DimensionType.Set, "Unsupported data"

    x = array[:]
    z = np.ones_like(x) * 0.8 * (hint or 0.5) + 0.1
    if second_y:
        ax2 = axis.twinx()
        ax2.set_ylim([0, 1])
        ax2.scatter(x, z, 50, color, linewidths=2, label=array.name, marker="|")
        ax2.set_yticks([])

        if labels is not None:
            for i, v in enumerate(labels[:]):
                ax2.annotate(str(v), (x[i], z[i]))

    else:
        #x = array[xlim or Ellipsis]
        axis.set_ylim([0, 1])
        axis.scatter(x, z, 50, color, linewidths=2, label=array.name, marker="|")
        axis.set_xlabel('%s [%s]' % (array.label, array.unit))
        axis.set_ylabel(array.name)
        axis.set_yticks([])

        if labels is not None:
            for i, v in enumerate(labels[:]):
                axis.annotate(str(v), (x[i], z[i]))


def plot_array_2d(array, axis, color=None, xlim=None, downsample=None, hint=None, labels=None):
    d1 = array.dimensions[0]
    d2 = array.dimensions[1]

    d1_type = d1.dimension_type
    d2_type = d2.dimension_type

    assert d1_type == nix.DimensionType.Sample, "Unsupported data"
    assert d2_type == nix.DimensionType.Sample, "Unsupported data"

    z = array[:]
    x_start = d1.offset or 0
    y_start = d2.offset or 0
    x_end = x_start + array.shape[0] * d1.sampling_interval
    y_end = y_start + array.shape[1] * d2.sampling_interval

    axis.imshow(z, origin='lower', extent=[x_start, x_end, y_start, y_end])
    axis.set_xlabel('%s [%s]' % (d1.label, d1.unit))
    axis.set_ylabel('%s [%s]' % (d2.label, d2.unit))
    axis.set_title(array.name)
    bar = plt.colorbar()
    bar.label('%s [%s]' % (array.label, array.unit))


def plot_array_2d_set(array, axis, color=None, xlim=None, downsample=None, hint=None, labels=None):
    d1 = array.dimensions[0]
    d2 = array.dimensions[1]

    d1_type = d1.dimension_type
    d2_type = d2.dimension_type

    assert d1_type == nix.DimensionType.Set, "Unsupported data"
    assert d2_type == nix.DimensionType.Sample, "Unsupported data"

    x_start = d2.offset or 0
    x_one = x_start + np.arange(0, array.shape[1]) * d2.sampling_interval
    x = np.tile(x_one.reshape(array.shape[1], 1), array.shape[0])
    y = array[:]
    axis.plot(x, y.T, color=color)
    axis.set_title(array.name)
    axis.set_xlabel('%s [%s]' % (d2.label, d2.unit))
    axis.set_ylabel('%s [%s]' % (array.label, array.unit))

    if d1.labels is not None:
        axis.legend(d1.labels)

