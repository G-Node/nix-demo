## About the pvc-6 converter

### How to start the converter

In order to convert a pvc-6 use-case file the converter has to be executed with the following parameters:

```bash
convert_pvc6.py -i INPUT -o OUTPUT [-s START] [-e END]
```

Where `INPUT` refers to an original use-case file as provided on http://crcns.org . 
`OUTPUT` is the name of the nix file that should be written (overwrites the file). 
`START` and `END` can be used to define the first and last sweep that should be read from the original file.
Use the parameter `--help` to get a information about the usage of the converter.

### Original pvc-6 file

The original pvc-6 file contains a series of data sets named Sweep_X where X is the number of the sweep.
Each sweep data set consists of two columns one containing the injected current and one the measured membrane voltage.
Each row represents one sample and the sampling interval is specified with 0.005 ms.

###### Example:

current | voltage
--------|--------
0.0     | 74.3
0.0     | 74.2
0.0     | 74.4
0.5     | 74.5
0.5     | 74.3
0.5     | 74.2
0.75    | 74.4
0.75    | 74.5
0.75    | 74.3

### How it is converted to nix

For every change in the current, the converter script calculates the start time, the duration and the value of the 
injected current.
From this data a multi tag is created: the start times are set as positions, the durations as extent and the array with 
the currents is used to add a feature to the tag.
The voltage of each swipe is stored as normal data array with a sampled dimension. 
It is named after the original sweep.
The data array is further referenced by the stimulus tag.

###### Example:

The following example shows how the stimulus would look like for the above table:

```
-- Stimulus X
   |-- positions: [0.0, 0.015, 0.03]
   |-- extents: [0.015, 0.015, 0.015]
   |-- features
       |-- data: [0.0, 0.5, 0.75]
       |-- link_type = indexed
```

### Some notes

The converter stores the stimulus in a less redundant way and saves therefore over 50% space after it is converted.
