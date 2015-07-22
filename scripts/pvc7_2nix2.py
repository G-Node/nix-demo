"""
Example usage:
python pvc7_2nix.py -p "/home/andrey/data/CRCNS/pvc-7" -s 5000 -e 6000
"""

import argparse
import os
import sys

import nix2
from pvc7_parser import Parser


def create_array(target_file, where, array_params, data, ticks):
    """
    A helper function.
    Creates a NIX array in a given <target_file> inside a given <where> block
    using provided <params>. Appends <ticks> as a first dimension.

    :param target_file:     full path to the target NIX file
    :param where:           nix::Block name
    :param array_params:    list of parameters to create a Matrix
    :param data:            actual data to store
    :param ticks:           ticks for the first dimension
    :return:
    """
    target = nix2.File(target_file, nix2.FileMode.ReadWrite)
    block = target.blocks[where]

    mtx = block.create_matrix_list(*array_params)
    mtx.all_data[:] = data

    mtx.dimensions[0].label = 'frames'
    for i in range(len(mtx.all_data.shape) - 1):
        mtx.append_set_dimension()

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

    f = nix2.File(args.output, nix2.FileMode.Overwrite)
    b = f.create_block(bname, bname)

    # convert 2-photon imaging
    # data is 3D: time, pixel X, pixel Y
    source_file = os.path.join(l_path, 'concat_31Hz.h5')
    data, ticks = Parser.read_imaging(source_file, start, end, resize)

    d1 = nix2.D('ms', 'Time', scale=ticks)
    d2 = nix2.D('px', 'Pixel', interval=1)
    mtl1 = b.create_matrix_list('concat', 'imaging', (d1, d2, d2), dtype=data.dtype, size=(1,) + data.shape)
    mtl1.all_data[:] = [data]

    # convert eye movie
    videofile = os.path.join(l_path, 'eye.avi')
    framesfile = os.path.join(l_path, 'eye_times.txt')
    data, ticks = Parser.read_movie(videofile, framesfile, start, end, resize)

    d1 = nix2.D('ms', 'Time', scale=ticks)
    d2 = nix2.D('px', 'Pixel', interval=1)
    d3 = nix2.D('bit', 'RGB', interval=1)
    mtl2 = b.create_matrix_list('eye.avi', 'movie', (d1, d2, d2, d3), dtype=data.dtype, size=(1,) + data.shape)
    mtl2.all_data[:] = [data]

    # convert mouse movie
    videofile = os.path.join(l_path, 'mouse.avi')
    framesfile = os.path.join(l_path, 'mouse_times.txt')
    data, ticks = Parser.read_movie(videofile, framesfile, start, end, resize)

    d1 = nix2.D('ms', 'Time', scale=ticks)
    d2 = nix2.D('px', 'Pixel', interval=1)
    d3 = nix2.D('bit', 'RGB', interval=1)
    mtl3 = b.create_matrix_list('mouse.avi', 'movie', (d1, d2, d2, d3), dtype=data.dtype, size=(1,) + data.shape)
    mtl3.all_data[:] = [data]

    # convert running speeds
    source_file = os.path.join(l_path, 'runspeed.txt')
    data, ticks = Parser.read_speed(source_file, start, end)

    d1 = nix2.D('ms', 'Time', scale=ticks)
    mtl4 = b.create_matrix_list('runspeed', 'runspeed', (d1,), dtype=data.dtype, size=(1,) + data.shape)
    mtl4.all_data[:] = [data]
    mtl4.unit = 'cm/s'
    mtl4.label = 'speed'

    # convert stimulus
    source_file = os.path.join(l_path, 'stimulus.csv')
    collected = Parser.read_stimulus(source_file, start, end)

    # create a reference between stimulus and recorded data
    rec = b.create_region_list("recording", "recording", (nix2.D('ms'),), dtype=collected.dtype, size=len(collected))
    # nix2 requires to wrap every single value into an array
    rec.all_data[:] = [[[x] for x in row] for row in collected[:,0:2]]

    # store stimulus combinations as point list
    stimulus = collected[:,2:6]

    d1 = nix2.D('deg', 'orientation')
    d2 = nix2.D('mm', 'SF')
    d3 = nix2.D('mm', 'TF')
    d4 = nix2.D('percent', 'contrast')
    combinations = b.create_point_list('stimulus', 'stimulus', (d1, d2, d3, d4), dtype=collected.dtype, size=len(stimulus))
    combinations.all_data[:] = stimulus

    # tag all data
    rec.add_feature_points(combinations)
    for ml in (mtl1, mtl2, mtl3, mtl4):
        rec.add_target_matrix(ml[0])

    f.close()