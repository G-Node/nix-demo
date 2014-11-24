# !/usr/bin/env python
#  -*- coding: utf-8 -*-
from __future__ import print_function, division

import nix
import math
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class Playback(object):
    
    def __init__(self, fig, video_array, tracking_tag=None, show_orientation=False):
        self.figure = fig
        self.axis = fig.add_subplot(111)
        self.im = None

        self.data = video_array
        self.height, self.width, self.channels, self.nframes = self.data.shape
        dim = video_array.dimensions[-1]
        ticks = dim.ticks
        self.interval = np.mean(np.diff(ticks))
        
        self.tag = tracking_tag
        if self.tag is not None:
            self.positions = self.tag.positions
            self.orientations = self.tag.features[0].data
            self.tracked_indices = self.__track_indices(ticks, self.positions[:,3])
            self.x = self.positions[:,0]
            self.y = self.positions[:,1]
            self.track_counter = 0
            self.draw_orientation = show_orientation
    
    def __track_indices(self, ticks, times):
        indices = np.zeros_like(times)
        for i,t in enumerate(times):
            indices[i] = np.argmin(np.abs(np.asarray(ticks) - t*1000))   
        return indices

    def __draw_circ(self, frame, x_pos, y_pos):
        radius = 8
        y, x = np.ogrid[-radius: radius, -radius: radius]
        index = x**2 + y**2 <= radius**2
        frame[y_pos-radius:y_pos+radius, x_pos-radius:x_pos+radius, 0][index] = 255
        frame[y_pos-radius:y_pos+radius, x_pos-radius:x_pos+radius, 1][index] = 0
        frame[y_pos-radius:y_pos+radius, x_pos-radius:x_pos+radius, 2][index] = 0
        return frame
     
    def __draw_line(self, frame, x, y, phi):
        length = 20
        dx = math.sin(phi/360.*2*np.pi) * length
        dy = math.cos(phi/360.*2*np.pi) * length
        cv2.line(frame, (int(x-dx),int(y+dy)),
                 (int(x+dx), int(y-dy)), (250,255,0), 2)
        return frame

    def grab_frame(self, i):
        frame = self.data[:,:,:,i]
        if self.tag is not None:
            if i in self.tracked_indices:
                frame = self.__draw_circ(frame, self.x[self.track_counter], 
                                         self.y[self.track_counter]) 
                if self.draw_orientation: 
                    frame = self.__draw_line(frame,self.x[self.track_counter], 
                                             self.y[self.track_counter],
                                             self.orientations[self.track_counter])
                self.track_counter += 1
        if self.im == None:
            im = self.axis.imshow(frame)
        else:
            im.set_data(frame)
        return im, 

    def start(self):
        ani = animation.FuncAnimation(self.figure, self.grab_frame,
                                      range(1,self.nframes,1), interval=self.interval, 
                                      repeat=False, blit=True)
        plt.show()


if __name__ == '__main__':
    import nix
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
        
    nix_file = nix.File.open('../data/tracking_data.h5', nix.FileMode.ReadOnly)
    b = nix_file.blocks[0]
    video = [a for a in b.data_arrays if a.name == "video"][0]
    tag = [t for t in b.multi_tags if t.name == "tracking"][0]
    
    fig = plt.figure(facecolor='white')
    pb = Playback(fig, video, tracking_tag=tag, show_orientation=True)
    pb.start()
    nix_file.close()
