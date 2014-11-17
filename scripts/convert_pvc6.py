#!/usr/bin/env python

import h5py
import sys
import nix
import numpy as np

SAMPLING_INTERVAL = 0.005
SAMPLING_UNIT = "ms"

index_to_time = lambda index: SAMPLING_INTERVAL * index
index_to_time_vec = np.vectorize(index_to_time)


class Sweep(object):
    """Contains the data of a sweep"""

    def __init__(self, name, number, data, times, durations, indexes, stimulus):
        self.name = name            # the original sweep name
        self.number = number        # the sweep number
        self.data = data            # the recorded voltage
        self.times = times          # times when the stimulus started
        self.durations = durations  # the duration of each stimulus
        self.indexes = indexes      # index when the stimulus changed
        self.stimulus = stimulus    # stimulus values (injected current)


def read_pvc6(in_file, start, end):
    """Read a pvc-6 file and return an array of Sweep objects"""
    pvc6_orig = h5py.File(in_file)

    sweeps = []
    for sweep_no in xrange(start, end):
        ds_name = "Sweep_%d" % sweep_no

        ds = pvc6_orig.get(ds_name, default=None)

        if ds is None:
            break

        size = ds.shape[0]
        volt_raw = ds[0:size, 1]
        stim_raw = ds[0:size, 0]

        rolled = np.roll(stim_raw, 1)
        rolled[0] = -1

        indexes = np.argwhere(stim_raw - rolled).flatten()
        stimulus = stim_raw[indexes]
        times = index_to_time_vec(indexes)

        rolled = np.roll(times, -1)
        rolled[-1] = index_to_time(size - 1)
        durations = rolled - times

        sweep = Sweep(ds_name, sweep_no, volt_raw, times, durations, indexes, stimulus)
        sweeps.append(sweep)

    return sweeps


def write_pvc6(sweeps, out_file):
    """Write an array of sweeps to a nix file"""

    f = nix.File.open(out_file, nix.FileMode.Overwrite)

    # basic nix file
    block = f.create_block("Session 01", "nix.session")

    curr_tag = None
    curr_stim = np.array([])
    curr_times = np.array([])

    # assume that all sweeps are sorted by sweep number and
    # therefore grouped by stimulus condition (see original pvc-6 file)
    for sweep in sweeps:

        print("Processing Sweep %02d / sample_count: %07d / stim_count: %05d / "
              "stim_times_count: %05d / stim_value_count: %05d" %
              (sweep.number, len(sweep.data), len(sweep.indexes), len(sweep.times), len(sweep.stimulus)))

        if not np.array_equal(curr_stim, sweep.stimulus) or not np.array_equal(curr_times, sweep.times):

            curr_stim = sweep.stimulus
            curr_times = sweep.times

            pos = block.create_data_array("Stimulus Positions %02d" % sweep.number, "nix.positions",
                                          data=sweep.indexes)
            pos.label = "time"
            pos.unit = SAMPLING_UNIT
            pos.append_set_dimension()

            ext = block.create_data_array("Stimulus Durations %02d" % sweep.number, "nix.extents",
                                          data=sweep.durations)
            ext.label = "time"
            ext.unit = SAMPLING_UNIT
            ext.append_set_dimension()

            curr_tag = block.create_multi_tag("Stimulus %02d" % sweep.number, "nix.stimulus", pos)
            curr_tag.extents = ext

            stim = block.create_data_array("Stimulus Current %02d" % sweep.number, "nix.stimulus.features",
                                           data=sweep.stimulus)
            stim.unit = "pA"
            stim.label = "injected current"

            curr_tag.create_feature(stim, nix.LinkType.Indexed)

        volt = block.create_data_array("Sweep %02d" % sweep.number, "nix.regular_sampled.time_series",
                                       data=sweep.data)
        volt.unit = "mV"
        volt.label = "membrane voltage"
        dim = volt.append_sampled_dimension(SAMPLING_INTERVAL)
        dim.unit = SAMPLING_UNIT
        dim.label = "time"

        curr_tag.references.append(volt)

    f.close()


def convert(in_file, out_file, start, end):
    """
    Converts a pvc-6 example file to nix

    :param in_file:     The name of the original pvc-6 file.
    :param out_file:    The name of the nix output file.
    :param start:       The number of first sweep to read.
    :param end:         The number of the sweep where reading should stop (excluding this number)
    """
    sweeps = read_pvc6(in_file, start, end)
    write_pvc6(sweeps, out_file)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Convert an hdf5 file from pvc-6 to a nix file")
    parser.add_argument("-i", "--in", dest="input", required=True,
                        help="Input hdf5 file from pvc-6 dataset")
    parser.add_argument("-o", "--out", dest="output", required=True,
                        help="Output nix file")
    parser.add_argument("-s", "--start", dest="start", default=0, type=int,
                        help="The number of the first sweep to read")
    parser.add_argument("-e", "--end", dest="end", default=sys.maxint, type=int,
                        help="The number of the sweep where reading should stop (excludes this sweep)")

    args = parser.parse_args()

    convert(args.input, args.output, args.start, args.end)
