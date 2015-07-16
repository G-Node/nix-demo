"""
Example usage:
python pvc7_2nix.py -p "/home/andrey/data/CRCNS/pvc-7" -s 5000 -e 6000
"""

import argparse
import os
import sys

import nix
from pvc7_parser import Parser


def create_array(target_file, where, array_params, ticks):
    """
    A helper function.
    Creates a NIX array in a given <target_file> inside a given <where> block
    using provided <params>. Appends <ticks> as a first dimension.

    :param target_file:     full path to the target NIX file
    :param where:           nix::Block name
    :param array_params:    list of parameters to create an array
    :param ticks:           ticks for the first dimension
    :return:
    """
    target = nix.File.open(target_file, nix.FileMode.ReadWrite)
    block = target.blocks[where]

    data = block.create_data_array(*array_params)

    data.append_range_dimension(ticks)
    data.dimensions[0].label = 'frames'
    for i in range(len(data.data.shape) - 1):
        data.append_set_dimension()

    target.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Conversion')

    parser.add_argument('-p', "--path", dest='path', required=True, type=str,
                        help="Path to the dataset folder")
    parser.add_argument("-o", "--out", dest="output",
                        default='../data/pvc-7.nix.h5', help="Output nix file")
    parser.add_argument("-s", "--start", dest="start", default=0, type=int,
                        help="The number of the first sweep to read")
    parser.add_argument("-e", "--end", dest="end", default=sys.maxint, type=int,
                        help="The number of the sweep where reading should stop"
                             " (excludes this sweep)")
    parser.add_argument("-c", "--compression", dest="comp", default=10,
                        type=int, help="Video compression (10 will result in "
                                       "100 times)")
    args = parser.parse_args()

    start = args.start
    end = args.end
    resize = args.comp
    bname = 'pvc-7'
    l_path = os.path.join(args.path, '122008_140124_windowmix')

    # prepare NIX file
    assert(start < end)

    f = nix.File.open(args.output, nix.FileMode.Overwrite)
    f.create_block(bname, bname)
    f.close()

    # convert 2-photon imaging
    source_file = os.path.join(l_path, 'concat_31Hz.h5')
    data, ticks = Parser.read_imaging(source_file, start, end, resize)
    params = ('concat', 'imaging', data.dtype, data.shape, data)
    create_array(args.output, bname, params, ticks)

    # convert eye movie
    videofile = os.path.join(l_path, 'eye.avi')
    framesfile = os.path.join(l_path, 'eye_times.txt')
    data, ticks = Parser.read_movie(videofile, framesfile, start, end, resize)
    params = ('eye.avi', 'movie', data.dtype, data.shape, data)
    create_array(args.output, bname, params, ticks)

    # convert mouse movie
    videofile = os.path.join(l_path, 'mouse.avi')
    framesfile = os.path.join(l_path, 'mouse_times.txt')
    data, ticks = Parser.read_movie(videofile, framesfile, start, end, resize)
    params = ('mouse.avi', 'movie', data.dtype, data.shape, data)
    create_array(args.output, bname, params, ticks)

    # convert running speeds
    source_file = os.path.join(l_path, 'runspeed.txt')
    data, ticks = Parser.read_speed(source_file, start, end)
    params = ('runspeed', 'runspeed', data.dtype, data.shape, data)
    create_array(args.output, bname, params, ticks)

    target = nix.File.open(args.output, nix.FileMode.ReadWrite)
    rs = target.blocks[bname].data_arrays['runspeed']
    rs.unit = 'cm/s'
    rs.label = 'speed'
    target.close()

    # convert stimulus
    source_file = os.path.join(l_path, 'stimulus.csv')
    collected = Parser.read_stimulus(source_file, start, end)

    target = nix.File.open(args.output, nix.FileMode.ReadWrite)
    block = target.blocks[bname]

    stimulus = collected[:,2:6]
    params = ('stimulus', 'stimulus', stimulus.dtype,
              stimulus.shape, stimulus)
    combinations = block.create_data_array(*params)
    dim = combinations.append_set_dimension()
    dim.labels = ('orientation', 'SF', 'TF', 'contrast')

    # tag all data
    tag = block.create_tag('recording', 'recording', collected[:,0])
    tag.extent = collected[:,1]
    tag.create_feature(combinations, nix.LinkType.Tagged)

    for name in ('concat', 'eye.avi', 'mouse.avi', 'runspeed'):
        tag.references.append(block.data_arrays[name])
