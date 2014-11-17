"""
Installing OpenCV on Ubuntu 14.04
http://www.samontab.com/web/2014/06/installing-opencv-2-4-9-in-ubuntu-14-04-lts/


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
    assert(start_index < end_index)

    source = h5py.File(source_file, 'r')
    sliced = source['data'][start_index:end_index]
    ticks = numpy.linspace(start_index, end_index - 1, end_index - start_index)

    target = nix.File.open(target_file, nix.FileMode.ReadWrite)
    block = target.blocks[name]

    data = block.create_data_array('concat', 'imaging', sliced.dtype, sliced.shape)

    data.data.append(sliced)

    data.append_range_dimension(ticks)
    data.append_set_dimension()
    data.append_set_dimension()

    map(lambda x: x.close(), [source, target])


def convert_eye(videofile, framesfile, target_file, start_index, end_index, name):
    """
    Convert a slice [start_index, end_index] of video recording into target
    NIX file.

    :param videofile:   path to the video file
    :param framesfile:  path to the mapping file
    :param target_file: path to the existing target NIX file
    :param start_index: index of the first image
    :param end_index:   index of the last image
    :param name:        name of the NIX block where to put the slice
    :return:
    """
    assert(start_index < end_index)

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

    print("\nconverting to NIX..")

    sliced = numpy.array(to_slice)
    data = block.create_data_array('eye', 'movie', sliced.dtype, sliced.shape, sliced)

    #data.data.append(sliced)

    data.append_range_dimension(ticks)
    data.append_set_dimension()
    data.append_set_dimension()
    data.append_set_dimension()

    map(lambda x: x.close(), [frames, target])
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Conversion')

    parser.add_argument('-p', "--path", dest='path', required=True, type=str,
                        help="Path to the dataset folder")
    parser.add_argument("-o", "--out", dest="output",
                        default='../data/pvc-7.h5', help="Output nix file")
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
    f = nix.File.open(args.output, nix.FileMode.Overwrite)
    f.create_block(bname, 'allendataset')
    f.close()

    # convert 2-photon imaging
    source_file = os.path.join(l_path, 'concat_31Hz.h5')
    convert_imaging(source_file, args.output, start, end, bname)

    # convert eye movie
    videofile = os.path.join(l_path, 'eye.avi')
    framesfile = os.path.join(l_path, 'eye_times.txt')
    convert_eye(videofile, framesfile, args.output, start, end, bname)