import copy, pickle, re, os, time, subprocess, datetime, itertools, sys, abc, argparse, matplotlib
matplotlib.use('agg')
from scipy import io as sciio
import numpy as np, pandas as pd, seaborn as sns
from numpy.testing import assert_almost_equal
from math import *
import matplotlib.pyplot as plt
from sklearn.neighbors import RadiusNeighborsRegressor
import matplotlib
from Bio import PDB
from sklearn.metrics import mean_squared_error
from sklearn import linear_model
from MDAnalysis import Universe
from MDAnalysis.analysis.align import *
from MDAnalysis.analysis.rms import rmsd
from MDAnalysis.analysis.distances import distance_array

'''This is the configuration file for all Python code in this directory,
it configures all default values/global parameters for constructors/functions
'''

#######################################################################
############   some global variables and helper functions  ############
#######################################################################

CONFIG_30 = "Alanine_dipeptide"     # the type of molecule we are studying
WARNING_INFO = "Comment out this line to continue."

def get_mol_param(parameter_list, molecule_name=CONFIG_30):   # get molecule specific parameter using a parameter list
    molecule_name_to_index = {"Alanine_dipeptide": 0, "Trp_cage": 1, "Src_kinase": 2,
                              "BetaHairpin": 3, "C24": 4}
    try:  result = parameter_list[molecule_name_to_index[molecule_name]]
    except: result = None
    return result

def get_index_list_with_selection_statement(pdb_file, atom_selection_statement):
    return (Universe(pdb_file).select_atoms(atom_selection_statement).indices + 1).tolist()

#######################################################################
##################   configurations  ##################################
#######################################################################

CONFIG_45 = 'keras'                         # training backend: "keras"
CONFIG_48 = 'Cartesian'           # input data type
CONFIG_76 = 'Cartesian'           # output data type
CONFIG_75 = get_mol_param([None, None, None, None, None])      # weights for the expected output (equivalent to modifying error functions)
CONFIG_52 = 64                # number of copies we generate for data augmentation
CONFIG_58 = False              # use representative points for training (generated by clustering)
CONFIG_59 = 500               # number of representative points

CONFIG_49 = get_mol_param([5.0, 20.0, 40.0, 20.0, 20.0]) # scaling factor for output for Cartesian coordinates
CONFIG_1 = ['../target/' + CONFIG_30] # list of directories that contains all coordinates files

CONFIG_57 = [
    get_index_list_with_selection_statement('../resources/alanine_dipeptide.pdb', 'name C or name CH3 or name CA or name N'),
    # get_index_list_with_selection_statement('../resources/alanine_dipeptide.pdb', 'not name H*'),
    get_index_list_with_selection_statement('../resources/1l2y.pdb', 'backbone and not name O'),
    # get_index_list_with_selection_statement('../resources/2src.pdb', 'backbone and not name O'),
    # get_index_list_with_selection_statement('../resources/2src.pdb',
    #                                         '(resid 144:170 or resid 44:58) and not name H*'),
    [ 694,  704,  714,  719,  729,  734,  744,  760,  764,  771,  783,
        793,  800,  810,  815,  825,  835,  842,  858,  869,  875,  891,
        897,  913,  919,  926, 2311, 2321, 2328, 2333, 2349, 2353, 2360,
       2367, 2379, 2389, 2404, 2413, 2420, 2432, 2451, 2461, 2466, 2473,
       2478, 2485, 2492, 2502, 2507, 2523, 2528, 2542, 2552, 2567, 2576,
       2586, 2593, 2600, 2610, 2626, 2632, 2648, 2651, 2661, 2666, 2685,
       2701, 2707, 2714, 2731],
    get_index_list_with_selection_statement('../resources/BetaHairpin.pdb', 'backbone and not name O'),
    get_index_list_with_selection_statement('../resources/C24.pdb', 'name C*')
]                                          # index list of atoms for training and biased simulations
temp_CONFIG_80 = get_mol_param([
    get_index_list_with_selection_statement('../resources/alanine_dipeptide.pdb', 'not name H*'),
    get_index_list_with_selection_statement('../resources/1l2y.pdb', 'backbone and not name O')
    ])
CONFIG_80 = [[temp_CONFIG_80[item_xx], temp_CONFIG_80[item_yy]]
              for item_xx in range(len(temp_CONFIG_80))
              for item_yy in range(item_xx + 1, len(temp_CONFIG_80))]    # pair index list for pairwise distances as input
if CONFIG_76 == 'pairwise_distance' or CONFIG_76 == 'combined':
    CONFIG_73 = get_mol_param(['name C or name CH3 or name CA or name N', 'name CA',
                               '(resid 144:170 or resid 44:58) and name CA', None
                               ])                         # atom selection for calculating pairwise distances, used only when it is in 'pairwise_distance' mode

CONFIG_17 = ['Tanh', 'Tanh', 'Tanh']  # types of hidden layers
CONFIG_78 = "Linear"                    # output layer type
CONFIG_79 = True                         # determine dimensionality of input/output of autoencoder automatically
CONFIG_2 = 1     # training data interval
if CONFIG_45 == 'keras':
    if CONFIG_76 == 'cossin':
        CONFIG_4 = get_mol_param([
            [.5,.4,0, True, [0.001, 0.001, 0.001, 0.001]] if CONFIG_17[1] == "Circular" else [0.3, 0.9, 0, True, [0.00, 0.1, 0.00, 0.00]]
        ])
    elif CONFIG_76 == 'Cartesian' or CONFIG_76 == 'combined':
        CONFIG_4 = get_mol_param([
            [.5, 0.5, 0, True, [0.00, 0.0000, 0.00, 0.00]],
            [0.3, 0.9, 0, True, [0.00, 0.0000, 0.00, 0.00]],
            [0.3, 0.9, 0, True, [0.00, 0.0000, 0.00, 0.00]],
            [0.3, 0.9, 0, True, [0.00, 0.0000, 0.00, 0.00]],
            [0.3, 0.9, 0, True, [0.00, 0.0000, 0.00, 0.00]],
            ])   # [learning rates, momentum, learning rate decay, nesterov, regularization coeff]
    elif CONFIG_76 == 'pairwise_distance':
        CONFIG_4 = get_mol_param([
            [0.3, 0.9, 0, True, [0.00, 0.0000, 0.00, 0.00]],
            [1.5, 0.9, 0, True, [0.00, 0.0000, 0.00, 0.00]], None, None
        ])
    else: raise Exception('error')
else:
    raise Exception('training backend not implemented')

CONFIG_5 = 200                   # max number of training epochs
CONFIG_6 = None                # filename to save this network
CONFIG_36 = 2                  #   dimensionality
CONFIG_37 = 2 * CONFIG_36 if CONFIG_17[1] == "Circular" else CONFIG_36      # number of nodes in bottleneck layer


CONFIG_71 = False                  # use mixed error function  (for Trp_cage only)
CONFIG_62 = get_mol_param([
    ['../resources/alanine_dipeptide.pdb', '../resources/alanine_ref_1.pdb'],
    ['../resources/1l2y.pdb', '../resources/Trp_cage_ref_1.pdb'] if not CONFIG_71 else ['../resources/1l2y.pdb', '../resources/1l2y.pdb'], # mixed_err
    # ['../resources/2src.pdb', '../resources/2src.pdb']
    ['../resources/2src.pdb'],
    ['../resources/BetaHairpin.pdb'], None
])                   # list of reference file
CONFIG_63 = get_mol_param([
    ['', '_1'],
    ['', '_1'],
    [''], [''], ['']
    ]
)                         # suffix for each reference configuration
CONFIG_61 = ['_aligned%s_coordinates.txt' % item
             for item in CONFIG_63]  # alignment_coor_file_suffix_list (we use different suffix for aligned files with respect to different references)
CONFIG_64 = get_mol_param([
    ['backbone', 'backbone'],
    ['backbone', 'backbone'] if not CONFIG_71 else ['backbone and resid 2:8', 'backbone'], # mixed_err
    # ['backbone and resid 144:170', 'backbone and resid 44:58']
    ['backbone'],
    ['backbone']
    ])                             # atom selection statement list for structural alignment
CONFIG_55 = len(CONFIG_61)                  # number of reference configurations used in training

CONFIG_3 = get_mol_param([       # the structure of ANN: number of nodes in each layer (input/output dim typically determined automatically)
    [0, 40, CONFIG_37, 40, 0],
    [0, 50, CONFIG_37, 50, 0],
    [0, 100, CONFIG_37, 100, 0],
    [0, 100, CONFIG_37, 100, 0],
    [0, 100, CONFIG_37, 100, 0],
])

CONFIG_74 = False                  # whether we start each biased simulation with nearest configuration or a fixed configuration
CONFIG_40 = 'implicit'                  # whether to include water molecules, option: explicit, implicit, water_already_included, no_water
CONFIG_51 = 'NVT'                  # simulation ensemble type
CONFIG_42 = False                             # whether to enable force constant adjustable mode
CONFIG_44 = True                             # whether to use hierarchical autoencoder
CONFIG_77 = 2                      # hierarchical autoencoder variant index
CONFIG_46 = False                             # whether to enable verbose mode (print training status)
CONFIG_47 = False                        # whether to set the output layer as circular layer
if CONFIG_47:
    raise Exception("Warning: this is a bad choice!  " + WARNING_INFO)

CONFIG_13 = 3                   # num of network trainings we are going to run, and pick the one with least FVE from them
CONFIG_43 = False    # whether we need to parallelize training part, not recommended for single-core computers
if CONFIG_43:
    raise Exception("Warning: parallelization of training is not well tested!  " + WARNING_INFO)

CONFIG_31 = 10        # maximum number of failed simulations allowed in each iteration

CONFIG_56 = get_mol_param([20, 8, 6, 6])    # number of biased simulations running in parallel
CONFIG_14 = 6  # max number of jobs submitted each time
CONFIG_29 = True  if CONFIG_40 == 'explicit' else False   # whether we need to remove the water molecules from pdb files
CONFIG_50 = False   # whether we need to preserve original file if water molecules are removed

CONFIG_10 = 10               # num of bins for get_boundary_points()
CONFIG_11 = 15                 # num of boundary points

CONFIG_39 = False    #  set the range of histogram automatically based on min,max values in each dimension
CONFIG_41 = False    # whether we reverse the order of sorting of diff_with_neighbors values in get_boundary algorithm

if CONFIG_17[1] == "Circular":
    CONFIG_18 = True  # whether we limit the boundary points to be between [-pi, pi], typically works for circularLayer
    CONFIG_26 = [[-np.pi, np.pi] for item in range(CONFIG_36)]    # range of PCs, for circular case, it is typically [[-np.pi, np.pi],[-np.pi, np.pi]]
elif CONFIG_17[1] == "Tanh":
    CONFIG_18 = False
    CONFIG_26 = [[-1, 1] for item in range(CONFIG_36)]
else:
    raise Exception('Layer not defined')

CONFIG_33 = CONFIG_3[0]   # length of list of cos/sin values, equal to the number of nodes in input layer
CONFIG_12 = '../target/' + CONFIG_30  # folder that contains all pdb files

CONFIG_65 = "US"          # default biasing method
CONFIG_16 = get_mol_param([500, 5000, 2000, 2000])                     # record interval (the frequency of writing system state into the file)
CONFIG_8 = get_mol_param([50000, 500000, 200000, 200000])                  # num of simulation steps
CONFIG_72 = 0             # enable fast equilibration
# following: for umbrella sampling
CONFIG_9 = get_mol_param([3000, 2000, 3000, 3000])                     # force constant for biased simulations
CONFIG_53 = 'fixed'                      # use fixed/flexible force constants for biased simulation for each iteration
CONFIG_54 = 2.50 * get_mol_param([30.0, 20.0, 15.0, 20.0, 20])             # max external potential energy allowed (in k_BT)
# following: for metadynamics
CONFIG_66 = 500             # pace of metadynamics
CONFIG_67 = 2               # height of metadynamics
CONFIG_68 = 0.1             # sigma of metadynamics
CONFIG_69 = 0               # whether to use well-tempered version
CONFIG_70 = 15              # biasfactor for well-tempered metadynamics
CONFIG_19 = '48:00:00'                                    # max running time for the sge job

CONFIG_21 = 300   # simulation temperature
CONFIG_22 = 0.002   # simulation time step, in ps

CONFIG_23 = get_mol_param(['CPU', 'CUDA', 'CUDA', 'CUDA'])              # simulation platform

temp_home_directory = subprocess.check_output('echo $HOME', shell=True).strip()
if temp_home_directory == "/home/kengyangyao":
    CONFIG_24 = 'local'  # machine to run the simulations
    CONFIG_25 = temp_home_directory + '/.anaconda2/lib/plugins'  # this is the directory where the plugin is installed
elif temp_home_directory == "/home/weichen9":
    CONFIG_24 = 'cluster'  # machine to run the simulations
    CONFIG_25 = temp_home_directory + '/.my_softwares/openmm7/lib/plugins'
elif temp_home_directory == "/u/sciteam/chen21":
    CONFIG_24 = 'local'
    CONFIG_25 = temp_home_directory + '/.openmm/lib/plugins'
else:
    print ('unknown user directory: %s' % temp_home_directory)

CONFIG_27 =  CONFIG_17[:2]  # layer_types for ANN_Force, it should be consistent with autoencoder
CONFIG_28 = "ANN_Force"    # the mode of biased force, it could be either "CustomManyParticleForce" (provided in the package) or "ANN_Force" (I wrote)

CONFIG_32 = 5000           # maximum force constant allowed (for force constant adjustable mode)
CONFIG_34 = 500            # force constant step, the value by which the force constant is increased each time (for force constant adjustable mode)
CONFIG_35 = 0.1            # distance tolerance, max distance allowed between center of data cloud and potential center (for force_constant_adjustable mode)
