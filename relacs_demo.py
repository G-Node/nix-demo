#!/usr/bin/env python
#  -*- coding: utf-8 -*-
from __future__ import print_function, division
import nix
import numpy as np
import matplotlib.pylab as plt
from utils.plotting import Plotter
from IPython import embed

def print_inventory(nix_file):
    print('File contents:')
    print('Blocks:\n')
    for b in nix_file.blocks:
        print('\t NAME: ' + b.name + '\t TYPE: ' + b.type + '\n')
        print('\t DATASETS:\n')
        for d in b.data_arrays:
            print('\t\t NAME: ' + d.name + '\t TYPE: ' + d.type + '\n')
        print('\t TAGS:\n')
        for t in list(b.tags) + list(b.multi_tags):
            print('\t\t Tag' + t.name + ' annotates: \n')
            for r in t.references:
                print('\t\t\t ' + r.name + '\n')
            print('\t\t as: ' + t.type) 


def tree_depth(section):
    depth = 1
    temp = []
    for s in section.sections:
        temp.append(tree_depth(s))
    depth += max(temp) if len(temp) > 0 else 0
    return depth 


def tree_structure(section, structure, depth):
    value_count = 0
    for p in section.items():
        value_count += len(p[1].values)
    structure.append((section, value_count, depth))
    for s in section.sections:
        structure = tree_structure(s, structure, depth+1)
    return structure


def make_table(section):
    columns = ['name', 'value', 'unit']
    cell_text = []
    for p in section.items():
        for i, v in enumerate(p[1].values):
            value = str(v.value)
            if len(value) > 10:
                value = value[:10]
            if i == 0:
                row_data = [p[0], value, p[1].unit if p[1].unit else '-']
            else:
                row_data = [p[0], value, p[1].unit if p[1].unit else '-']
            cell_text.append(row_data)
    if len(cell_text) > 0:
        nrows, ncols = len(cell_text)+1, len(columns)
        hcell, wcell = 0.3, 1.
        hpad, wpad = 0, 0    
        fig = plt.figure(figsize=(ncols*wcell+wpad, nrows*hcell+hpad))
        ax = fig.add_subplot(111)
        ax.axis('off')
        the_table = ax.table(cellText=cell_text,
                               colLabels=columns, 
                               loc='center')
        embed()
#    ax.set_title(section.name)
    return fig
        

if __name__ == '__main__':
    # open file
    nix_file = nix.File.open('data/relacs.h5')
    # list the contents of the dataset
    print_inventory(nix_file)
    voltage = [da for da in nix_file.blocks[0].data_arrays if da.name == "V-1"][0]
    eod = [da for da in nix_file.blocks[0].data_arrays if da.name == "EOD"][0]
    local_eod = [da for da in nix_file.blocks[0].data_arrays if da.name == "LocalEOD-1"][0]
    
    plt.plot(local_eod[3250000:3400000])
    plt.show()
    """
    # show some metadata
    fig = make_table([s for s in nix_file.blocks[0].metadata.sections if s.name == 'Cell'][0])
    fig.savefig('table.png')
    plt.show()
    
    fig = plt.figure(facecolor='white')
    plotter = Plotter(figure=fig)
    
    ax = fig.add_subplot(311)
    ax.tick_params(direction='out')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plotter.add_plot(voltage, axis=ax, xlim=[25000, 30000], down_sample=5)
    
    ax = fig.add_subplot(312)
    ax.tick_params(direction='out')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plotter.add_plot(eod, axis=ax, xlim=[25000, 30000], down_sample=5)
    
    ax = fig.add_subplot(313)
    ax.tick_params(direction='out')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plotter.add_plot(local_eod, axis=ax, xlim=[25000, 30000], down_sample=5)

    plt.show()
    """
    """
    # plot spike events
    spike_times = [da for da in nix_file.blocks[0].data_arrays if da.name == "spike times"][0]

    fig = plt.figure(facecolor='white')
    plotter = Plotter(figure=fig)
    
    ax = fig.add_subplot(111)
    ax.tick_params(direction='out')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plotter.add_plot(voltage, axis=ax, xlim=[0, 3000])
    plotter.add_plot(spike_times, axis=ax, xlim=[0, 3000])
    

    # plot stimulus events

    fig = plt.figure(facecolor='white')
    plotter = Plotter(figure=fig)
    
    ax = fig.add_subplot(312)
    ax.tick_params(direction='out')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    # plotter.add_plot(eod, axis=ax, xlim=[0, 3000])
    # plotter.add_plot(eod_times, axis=ax, xlim=[0, 3000])
    """

    plt.show()
    nix_file.close()
