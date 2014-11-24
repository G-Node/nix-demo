import nix
import scipy.io as sp
import numpy as np
from IPython import embed
import cProfile
    

def save_value(section, property_name, value, unit=None):
    v = nix.Value(value)
    p = section.create_property(property_name, [v])
    if unit is not None:
        p.unit = unit
    

def export_data_info(nix_file, block, block_info, name):
    sec = nix_file.create_section(name, "recording")
    for f in block_info.items():
        save_value(sec, f[0], f[1])
    block.metadata = sec


def export_stimulus_metadata(nix_file, block, stim_info, name):
    sec = nix_file.create_section(name, "stimulus")
    for i in stim_info.items():
        if isinstance(i[1], dict):
            subsec = sec.create_section(i[0], "parameter set")
            for j in i[1].items():
                save_value(subsec, j[0], j[1])
        else:
            save_value(sec, i[0], i[1])
    return sec
 

def export_spikes(nix_file, block, spike_data, stim_section, rec_no):
    data_arrays = []
    for i in range(spike_data.shape[0]):
        data = np.asarray(spike_data[i], dtype=np.float32)
        da = block.create_data_array('RGC_' + str(i) + '_stim_' + str(rec_no), 'nix.event.spike_time', data=data)
        da.label = 'time'
        da.unit = 's'
        da.append_set_dimension()
        data_arrays.append(da)
    return data_arrays


def convert_data_info(data_info, rec_no):
    info = {}
    for f in data_info.__dict__.keys():
        if f == "_fieldnames":
            continue
        elif f == "RecStartTime":
            info[f] = '-'.join(map(str, data_info.__dict__[f][rec_no,:]))
        elif f == 'RecNo':
            info[f] = float(data_info.__dict__[f][rec_no])
        else:
            if isinstance(data_info.__dict__[f], unicode):
                info[f] = str(data_info.__dict__[f])
            else:
                info[f] = data_info.__dict__[f]
    return info


def convert_stim_info(stim_info, rec_no):
    info = {}
    temp = stim_info[rec_no].__dict__
    for i in temp.items():
        if i[0] == "_fieldnames":
            continue
        if isinstance(i[1], sp.matlab.mio5_params.mat_struct):
            temp2 = i[1].__dict__
            info[i[0]] = {}
            for k in temp2.items():                
                if k[0] == "_fieldnames":
                    continue
                info[i[0]][k[0]] = k[1]
        elif isinstance(i[1], unicode):
            info[i[0]] = str(i[1])
        else:
            info[i[0]] = float(i[1])
    return info


def read_bit(f):
    bytes = (ord(b) for b in f.read())
    for b in bytes:
        for i in xrange(8):
            yield (b >> i) & 1


def load_stimulus(filename, stim_info):
    n_frames = stim_info['Nframes'] - 1
    n_x = stim_info['param']['x'] / stim_info['param']['dx']
    n_y = stim_info['param']['y'] / stim_info['param']['dy']
    m = n_x * n_y
    count = 0
    stim = np.zeros((m*n_frames), dtype=np.int8)
    with open(filename, 'r') as f:
        for b in read_bit(f):
            stim[count] = b;
            count += 1
            if count >= n_frames * m:
                break;
    temp = np.reshape(2*stim-1, (m, n_frames), order='F')
    return temp


def export_stimulus(nix_file, block, stimulus, stim_section, rec_no, data_arrays):
    stim_array = block.create_data_array('stimulus_' + str(rec_no) + '_data', 'nix.stimulus', data=stimulus)
    dim = stim_array.append_sampled_dimension(1.0)
    dim.label = 'lines'
    dim = stim_array.append_sampled_dimension(1.0/60)
    dim.label = 'time'
    dim.unit = 's'
    stim_array.metadata = stim_section
    
    position = [0, 0]
    extent = list(stimulus.shape)
    extent[-1] *= 1./60
    tag = block.create_tag('stimulus presentation', 'nix.event.segment', position)
    tag.extent = extent
    
    for da in data_arrays:
        tag.references.append(da)
    tag.create_feature(stim_array,nix.LinkType.Tagged)
    

def export_retina_data(filename, export_stim=False):
    data = sp.loadmat(filename, struct_as_record=False, squeeze_me=True)
    nix_file = nix.File.open(filename[:-3]+'nix', nix.FileMode.Overwrite)
    name = filename.split('/')[-1][:-4]

    for i in range(data["spikes"].shape[1]):
        block_name = name + "recording_" + str(i)
        print block_name
        block = nix_file.create_block(block_name, 'nix.recording_session')
        spike_times = data["spikes"][:,i]
        rec_info = convert_data_info(data['datainfo'], i)
        stim_info = convert_stim_info(data['stimulus'], i)
        export_data_info(nix_file, block, rec_info, block_name)
        stim_section = export_stimulus_metadata(nix_file, block, stim_info, "stimulus_" + str(i))
        spike_arrays = export_spikes(nix_file, block, spike_times, stim_section, i)
        
        if export_stim:
            stim_file = 'crcns_ret-1/ran1.bin'
            stimulus = load_stimulus(stim_file, stim_info)
            export_stimulus(nix_file, block, stimulus, stim_section, i, spike_arrays)    
    nix_file.close()

    
if __name__=='__main__':
    name = 'crcns_ret-1/Data/20080516_R1.mat'
    export_retina_data(name, export_stim=False)
