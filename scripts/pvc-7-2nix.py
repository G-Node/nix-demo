"""
Installing OpenCV on Ubuntu 14.04
http://www.samontab.com/web/2014/06/installing-opencv-2-4-9-in-ubuntu-14-04-lts/

Example:
python pvc-7-2nix.py -p "/home/andrey/data/CRCNS/pvc-7" -s 50000 -e 51000
"""

import h5py
import nix
import numpy
import argparse
import os
import sys
import cv2


def convert_imaging(source_file, target_file, start_index, end_index, name):
    """
    Get a slice [start_index, end_index] from source file and store it
    to target NIX file.

    :param source_file: full path to the source data file
    :param target_file: full path to the existing target NIX file
    :param start_index: index of the first image
    :param end_index:   index of the last image
    :param name:        name of the NIX block where to put the slice
    :return:
    """
    source = h5py.File(source_file, 'r')
    sliced = source['data'][start_index:end_index]
    ticks = numpy.linspace(start_index, end_index - 1, end_index - start_index)

    target = nix.File.open(target_file, nix.FileMode.ReadWrite)
    block = target.blocks[name]

    params = ('concat', 'imaging', sliced.dtype, sliced.shape, sliced)
    data = block.create_data_array(*params)

    data.append_range_dimension(ticks)
    data.append_set_dimension()
    data.append_set_dimension()

    map(lambda x: x.close(), [source, target])


def convert_movie(videofile, framesfile, target_file, start_index, end_index, name):
    """
    Convert a slice [start_index, end_index] of video recording into target
    NIX file. TODO - find a way to seek directly the slice

    :param videofile:   path to the video file
    :param framesfile:  path to the mapping file
    :param target_file: path to the existing target NIX file
    :param start_index: index of the first image
    :param end_index:   index of the last image
    :param name:        name of the NIX block where to put the slice
    :return:
    """
    cap = cv2.VideoCapture(videofile)
    frames = open(framesfile, 'r')

    print('reading video %s' % videofile)

    to_slice, ticks = [], []
    for line in frames.readlines():
        frame_no = int(line.split('.')[0])
        success, image = cap.read()

        print "\rprocessing frame %s.." % str(frame_no),

        if not success:
            break

        if start_index <= frame_no < end_index:
            to_slice.append(image)
            ticks.append(frame_no)

        if frame_no > end_index:
            break

    target = nix.File.open(target_file, nix.FileMode.ReadWrite)
    block = target.blocks[name]

    print "\rconverting to NIX..",

    sliced = numpy.array(to_slice)
    arr_name = os.path.basename(videofile)
    params = (arr_name, 'movie', sliced.dtype, sliced.shape, sliced)
    data = block.create_data_array(*params)

    data.append_range_dimension(ticks)
    data.append_set_dimension()
    data.append_set_dimension()
    data.append_set_dimension()

    map(lambda x: x.close(), [frames, target])
    cap.release()
    cv2.destroyAllWindows()

    print "done"


def convert_speed(source_file, target_file, start_index, end_index, name):
    """
    Get a slice [start_index, end_index] from source file and store it
    to target NIX file.

    :param source_file: full path to the source data file
    :param target_file: full path to the existing target NIX file
    :param start_index: index of the first image
    :param end_index:   index of the last image
    :param name:        name of the NIX block where to put the slice
    :return:
    """
    speeds = open(source_file, 'r')

    to_slice, ticks = [], []
    for i, line in enumerate(speeds.readlines()):
        if start_index <= i < end_index:
            to_slice.append(float(line))
            ticks.append(i)

    target = nix.File.open(target_file, nix.FileMode.ReadWrite)
    block = target.blocks[name]

    sliced = numpy.array(to_slice)
    ticks = numpy.array(ticks, dtype=int)
    params = ('runspeed', 'array', sliced.dtype, sliced.shape, sliced)
    data = block.create_data_array(*params)

    data.append_range_dimension(ticks)

    map(lambda x: x.close(), [speeds, target])


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
    args = parser.parse_args()

    start = args.start
    end = args.end
    bname = 'pvc-7'
    l_path = os.path.join(args.path, '122008_140124_windowmix')

    # prepare NIX file
    assert(start < end)

    f = nix.File.open(args.output, nix.FileMode.Overwrite)
    f.create_block(bname, 'allendataset')
    f.close()

    # convert 2-photon imaging
    source_file = os.path.join(l_path, 'concat_31Hz.h5')
    convert_imaging(source_file, args.output, start, end, bname)

    """
    # convert eye movie
    videofile = os.path.join(l_path, 'eye.avi')
    framesfile = os.path.join(l_path, 'eye_times.txt')
    convert_movie(videofile, framesfile, args.output, start, end, bname)

    # convert mouse movie
    videofile = os.path.join(l_path, 'mouse.avi')
    framesfile = os.path.join(l_path, 'mouse_times.txt')
    convert_movie(videofile, framesfile, args.output, start, end, bname)

    # convert running speeds
    source_file = os.path.join(l_path, 'runspeed.txt')
    convert_speed(source_file, args.output, start, end, bname)
    """

    # read stimulus
    source_file = os.path.join(l_path, 'stimulus.csv')
    stimfile = open(source_file, 'r')

    collector = []
    stimfile.readline()  # skip first line
    for i, line in enumerate(stimfile.readlines()):
        parse = lambda j, x: float(x) if j == 3 or j == 5 else int(x)
        collector.append([parse(j, x) for j, x in enumerate(line.split(','))])

    stimfile.close()

    collected = numpy.array(collector)
    collected = collected[collected[:,0].argsort()]  # sorting by positions
    si = numpy.where(collected[:,0] >= start)[0][0]
    ei = numpy.where(collected[:,0] < end)[0][-1]
    collected = collected[si:ei]  # slicing by region of interest

    # convert stimulus and tag data
    target = nix.File.open(args.output, nix.FileMode.ReadWrite)
    block = target.blocks[bname]

    stimulus = collected[:,2:6]
    params = ('combinations', 'stimulus', stimulus.dtype, stimulus.shape, stimulus)
    combinations = block.create_data_array(*params)

    tag = block.create_tag('stimulus', 'stimulus', collected[:,0])
    tag.extent = collected[:,1]
    tag.references.append(block.data_arrays['concat'])
    tag.create_feature(combinations, nix.LinkType.Tagged)