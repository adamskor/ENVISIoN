import inviwopy
# import inviwopy.glm as glm
import numpy as np
import h5py
from envisionpy.utils.exceptions import *
from .baseNetworks.VolumeSubnetwork import VolumeSubnetwork

class ElfSubnetwork(VolumeSubnetwork):
    '''
    Manages a subnetwork for electron localisation function (ELF) visualisation. 
    Uses a default VolumeSubnetwork.
    '''
    def __init__(self, inviwoApp, hdf5_path, hdf5_outport, xpos=0, ypos=0):
        VolumeSubnetwork.__init__(self, inviwoApp, hdf5_path, hdf5_outport, xpos, ypos, False)
        
        # Set basis and volume path
        with h5py.File(hdf5_path, "r") as h5:
            self.set_basis(np.array(h5["/basis/"], dtype='d'), h5['/scaling_factor'][()])
        self.set_hdf5_subpath("/ELF")
        self.set_volume_selection('/final')

        # Set some default parameters for elf visualisation.
        self.add_tf_point(0.45, [0.1, 0.1, 0.8, 0.05])
        self.add_tf_point(0.5, [0.2, 0.8, 0.1, 0.1])
        self.add_tf_point(0.8, [0.9, 0.1, 0.1, 0.5])

    @staticmethod
    def valid_hdf5(hdf5_file):
        return (
            hdf5_file.get('ELF') != None and 
            len(hdf5_file.get('ELF').keys()) != 0 and
            hdf5_file.get('basis') != None and 
            hdf5_file.get('scaling_factor') != None)

    def decoration_is_valid(self, vis_type):
        return vis_type in ['charge', 'elf', 'atom']
