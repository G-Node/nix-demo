#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division

import matplotlib.mlab as mlab
import numpy as np
import nix
import argparse


def create_sample_1d(block):
    delta = 0.1
    x = np.sin(np.arange(0, 10, delta))*10 - 60
    array = block.create_data_array("signal", "nix.data.sampled.V", nix.DataType.Double, (len(x), ))
    array.data[:] = x
    array.unit = 'mV'
    array.label = 'Volt'
    dim = array.create_sampled_dimension(1, delta)
    dim.label = 'time'
    dim.unit = 's'
    return array


def create_set_1d(block):
    array = block.create_data_array("spikes", "nix.events.position.Spikes-1", nix.DataType.Double, (10, ))
    array.data[:] = np.arange(0, 10)
    array.unit = 's'
    array.label = 'time'
    array.create_set_dimension(1)
    return array


def create_sample_2d(block):
    #from http://matplotlib.org/examples/pylab_examples/image_demo.html
    delta = 0.25
    x = np.arange(-3.0, 3.0, delta)
    y = np.arange(-3.0, 3.0, delta)
    X, Y = np.meshgrid(x, y)
    Z1 = mlab.bivariate_normal(X, Y, 1.0, 1.0, 0.0, 0.0)
    Z2 = mlab.bivariate_normal(X, Y, 1.5, 0.5, 1, 1)
    z = Z2-Z1+0.4  # difference of Gaussians

    array = block.create_data_array("rf", "nix.data.sampled.DF/F", nix.DataType.Double, (len(x), len(y)))
    array.data[:] = z

    d1 = array.create_sampled_dimension(1, delta)
    d1.unit = 's'
    d1.label = 'time'
    d1.offset = 0
    d2 = array.create_sampled_dimension(2, delta)
    d2.unit = 'mm'
    d2.label = 'location'
    d2.offset = -3.0
    array.unit = 'lm'
    array.label = 'intensity'
    return array


def create_set_sample_2d(block):
    delta = 0.1
    x = np.arange(0, 10, delta)
    n_samples = 4
    array = block.create_data_array("firing rate", "nix.data.sampled.spike_rate", nix.DataType.Double, (n_samples, len(x)))
    for i in range(n_samples):
        array.data[i, :] = (np.sin(x * (1+i)) + 1.0) * 5.0
    dim = array.create_set_dimension(1)
    dim.labels = ['frq: %d' % (i+1) for i in range(n_samples)]
    dim = array.create_sampled_dimension(2, delta)
    dim.unit = 's'
    dim.label = 'time'
    array.unit = 'Hz'
    array.label = 'spike rate'
    return array


def create_leibig_data(block, path):
    import csv
    fd = open(path, 'rb')
    lreader = csv.reader(fd, delimiter=',')
    ldata = np.array([[float(x) for x in r] for r in lreader])
    array = block.create_data_array("MEA LFP", "nix.data.sampled.lfp", nix.DataType.Double, ldata.shape)
    array.data[:] = ldata
    d1 = array.create_sampled_dimension(1, 7.4)
    d1.unit = 'um'
    d1.label = 'x'
    d1.offset = 0
    d2 = array.create_sampled_dimension(2, 14.8)
    d2.unit = 'um'
    d2.label = 'y'
    d2.offset = 0
    array.unit = 'mV'
    array.label = 'Volt'
    return array

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='NIX Plotter')
    parser.add_argument('--file', dest='file', type=str, default='demo.h5')
    parser.add_argument('--leibig', dest='leibig', type=str, default=None)
    args = parser.parse_args()

    nf = nix.File.open(args.file, nix.FileMode.Overwrite)
    session = nf.create_block("test block", "recordingsession")
    da = create_sample_1d(session)
    print('1-D, SampleDD: %s' % da.id)
    da = create_set_1d(session)
    print('1-D, SetD: %s' % da.id)
    da = create_sample_2d(session)
    print('2-D, SampleD: %s' % da.id)
    da = create_set_sample_2d(session)
    print('2-D, SetD+SampleD: %s' % da.id)

    if args.leibig is not None:
        da = create_leibig_data(session, args.leibig)
        print('Leibig 2-D, SampleD+SampleD: %s' % da.id)