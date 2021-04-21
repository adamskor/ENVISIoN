import os,sys
import inspect
path_to_current_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.expanduser(path_to_current_folder+'/..'))
import re
import numpy as np
import h5py
from h5writer import _write_basis, _write_scaling_factor, _write_coordinates, _write_forces
from pathlib import Path

def parse_lattice(ELK_dir):
    basis = []
    with open(os.path.join(ELK_dir,'INFO.OUT'), "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "Lattice vectors :" in line:
                basis.append([float(n) for n in lines[i+1].split()[:3]])
                basis.append([float(n) for n in lines[i+2].split()[:3]])
                basis.append([float(n) for n in lines[i+3].split()[:3]])
            if "Unit cell volume      :" in line:
                list = line.split()
                scaling_factor = -float(list[-1])
    return scaling_factor ,basis

def parse_coordinates(ELK_dir, number_of_atoms):
    coords_list = []
    with open(os.path.join(ELK_dir,'INFO.OUT'), "r") as f:
        lines = f.readlines()
        counter = 0
        for i, line in enumerate(lines):
            if "atomic positions" in line:
                n = 0
                while n < number_of_atoms[counter]:
                    list_of_line = lines[i+1+n].split()[2:5]
                    coords_list += [list_of_line]
                    n += 1
                counter += 1
        for x in range(len(coords_list)):
            for y in range(len(coords_list[x])):
                coords_list[x][y] = float(coords_list[x][y])
    return coords_list

def find_elements( ELK_dir):
    elements = []
    number_of_atoms = []
    with open(os.path.join(ELK_dir,"EQATOMS.OUT"), "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "Species" in line:
                list_of_word_in_line = line.split()
                for word in list_of_word_in_line:
                    if "(" in word:
                        word = word.replace("(","")
                        word = word.replace(")","")
                        elements += [word]
                list_of_word_in_line = lines[i+2].split()
                number_of_atoms += [len(list_of_word_in_line)]
    return elements, number_of_atoms


def force_parser(hdf5_file, ELK_dir):
    if os.path.isfile(h5file):
        with h5py.File(h5file, 'r') as h5:
            if "/Forces" in h5:
                print("Already parsed. Skipping.")
                return True
            h5.close()
            
    elements, number_of_atoms = find_elements(ELK_dir)
    scaling_factor, basis = parse_lattice(ELK_dir)
    coords_list = parse_coordinates(ELK_dir, number_of_atoms)


    return
