"""
Installing OpenCV on Ubuntu 14.04
http://www.samontab.com/web/2014/06/installing-opencv-2-4-9-in-ubuntu-14-04-lts/

Example:
python pvc-7-2nix.py -p "/home/andrey/data/CRCNS/pvc-7" -s 5000 -e 6000
"""

import h5py
import numpy
import argparse
import os
import sys
from PIL import Image

import nix
import cv2


def process_image(image, resize):
    """
    Resizes image by a given scale <resize>.

    :param image:   image as numpy array
    :param resize:  scale to resize
    :return:
    """
    if resize is None:
        return image

    img = Image.fromarray(image)
    rsize = img.resize((img.size[0]/resize, img.size[1]/resize))

    return numpy.asarray(rsize)


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
    for i in range(len(data.data.shape) - 1):
        data.append_set_dimension()

    target.close()


class Parser(object):

    @staticmethod
    def read_imaging(source_file, start_index, end_index, resize=None):
        """
        Read a slice [start_index, end_index] from source imaging file.

        :param source_file: full path to the source data file
        :param start_index: index of the first image
        :param end_index:   index of the last image
        :return:
        """
        source = h5py.File(source_file, 'r')
        data = source['data'][start_index:end_index]
        data = [process_image(x, resize) for x in data]
        ticks = numpy.linspace(start_index, end_index - 1, end_index - start_index)

        source.close()

        return numpy.array(data), ticks

    @staticmethod
    def read_movie(videofile, framesfile, start_index, end_index, resize=None):
        """
        Read a slice [start_index, end_index] of video recording.

        :param videofile:   path to the video file
        :param framesfile:  path to the mapping file
        :param start_index: index of the first image
        :param end_index:   index of the last image
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
                to_slice.append(process_image(image, resize))
                ticks.append(frame_no)

            if frame_no > end_index:
                break

        print "done"

        return numpy.array(to_slice), numpy.array(ticks, dtype=int)

    @staticmethod
    def read_speed(source_file, start_index, end_index):
        """
        Read a slice [start_index, end_index] from file with mouse speeds.

        :param source_file: full path to the source data file
        :param start_index: index of the first image
        :param end_index:   index of the last image
        :return:
        """
        speeds = open(source_file, 'r')

        to_slice, ticks = [], []
        for i, line in enumerate(speeds.readlines()):
            if start_index <= i < end_index:
                to_slice.append(float(line))
                ticks.append(i)

        speeds.close()

        return numpy.array(to_slice), numpy.array(ticks, dtype=int)

    @staticmethod
    def read_stimulus(source_file, start_index, end_index):
        """
        Read a slice [start_index, end_index] from stimulus file.

        :param source_file: full path to the source data file
        :param start_index: index of the first image
        :param end_index:   index of the last image
        :return:
        """
        stimfile = open(source_file, 'r')

        collector = []
        stimfile.readline()  # skip first line
        for i, line in enumerate(stimfile.readlines()):
            parse = lambda j, x: float(x) if j == 3 or j == 5 else int(x)
            collector.append([parse(j, x) for j, x in enumerate(line.split(','))])

        stimfile.close()

        collected = numpy.array(collector)
        collected = collected[collected[:,0].argsort()]  # sorting by positions
        si = numpy.where(collected[:,0] >= start_index)[0][0]
        ei = numpy.where(collected[:,0] < end_index)[0][-1]

        return collected[si:ei]  # slicing by region of interest


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
