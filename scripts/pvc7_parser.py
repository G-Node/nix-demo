"""
Installing OpenCV on Ubuntu 14.04
http://www.samontab.com/web/2014/06/installing-opencv-2-4-9-in-ubuntu-14-04-lts/

Working with video with OpenCV
http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_gui/py_video_display/py_video_display.html#display-video
http://docs.opencv.org/trunk/modules/highgui/doc/reading_and_writing_images_and_video.html

Image processing with PIL
http://matplotlib.org/users/image_tutorial.html
"""

import h5py
import numpy
import cv2

from PIL import Image


class Parser(object):

    @staticmethod
    def _process_image(image, resize):
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
        data = [Parser._process_image(x, resize) for x in data]
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
                to_slice.append(Parser._process_image(image, resize))
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
