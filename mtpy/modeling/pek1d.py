# -*- coding: utf-8 -*-
"""
Created on Fri Mar 14 10:21:05 2014

@author: Alison Kirkby

"""

import os
import mtpy.utils.filehandling as fh
import mtpy.utils.elevation_data as mted
import pek1dclasses as pek1dc
from sys import argv
from subprocess import call


def generate_inputfiles(epath, **input_parameters):
    
    """
    generate input files for a model. 
    
    -----------------------Compulsory parameter--------------------------------
    **epath** the full path to the edi file.
    
    -----------------------Recommended parameter-------------------------------
    **wd** working directory, default is the edi directory. A new directory
           is created under this directory to put all the input files into

    ------------------------Optional Parameters--------------------------------
    **datafile** name for the input file, if not specified, name is taken from
                 the edi file
    **errorfloor_z** error floor for the input z values, can be an absolute
                     value or relative (e.g. 0.1 means 10%)
                     default is 0.1
    **errorfloor_type** type of error floor, either 'relative' or 'absolute'
                        default is relative.
    **type_struct** type of structure penalty, default is 6
    **type_aniso** type of anisotropy penalty, default is 2
    **value_struct** structural penalty weights to apply, default is [1,10,100]
    **value_aniso** anisotropy penalty weights to apply, default is [1,10,100]
    **imax** maximum number of iterations to run, default is 100


    to generate an a priori (inmodel) file, need to put keyword
    **build_inmodel** = True, default is False
    
    also need to specify the following parameters:
    **inmodel_vals**
    

    
    inmodel_modeldir = string, folder containing previous model run with same 
    resolution, necessary for constructing the layer depths in the inmodel file.
    inmodel_vals = dictionary structured as follows:
    {layer top depth:[minimum_resistivity, maximum_resistivity, strike]}
    
    """
    import pek1d
    
    data_kwds = ['working_directory','datafile', 'errorfloor', 
                 'errorfloor_type', 'edipath', 'mode']
    control_kwds = ['penalty_type_structure', 'penalty_type_anisotropy',
                    'penalty_weight_structure', 'penalty_weight_anisotropy', 
                    'iteration_max']
    inmodel_kwds = ['inmodel_dictionary','inmodel_modeldir']

    data_inputs = {'epath':epath}
    control_inputs = {}
    inmodel_inputs = {}
    
    build_inmodel = False
    for key in input_parameters.keys():
        print key
        if key in data_kwds:
            data_inputs[key] = input_parameters[key]
        if key in control_kwds:
            control_inputs[key] = input_parameters[key]
        if key in inmodel_kwds:
            inmodel_inputs = input_parameters[key]
        if key == 'build_inmodel':
            build_inmodel = input_parameters[key]


    Data = pek1dc.Data(**data_inputs)
    # make a save path to match the edi file
    savepath = fh.make_unique_folder(Data.wd,os.path.basename(Data.epath)[:5]+Data.mode)
    Data.write_datafile(wd = savepath)
    
    # update the working directory to the new savepath
    control_inputs['wd'] = savepath
    inmodel_inputs['wd'] = savepath
    
    Ctl = pek1dc.Control(**control_inputs)
    Ctl.write_ctlfile()
    
    if build_inmodel:
        if 'inmodel_modeldir' in input_parameters.keys():
            inmodel_dict = pek1d.create_inmodel_dictionary_from_file(input_parameters['inmodel_parameters_file'],
                                                               Data.x,Data.y,
                                                               working_directory = None)                                      
            Inmodel = pek1dc.Inmodel(input_parameters['inmodel_modeldir'],
                                     inmodel_dictionary = inmodel_dict)
            Inmodel.write_inmodel()
    
    return Data


def parse_arguments(arguments):
    """
    takes list of command line arguments obtained by passing in sys.argv
    reads these and returns a parser object
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(description = 'Set up and run a set of 1d anisotropic model runs')
    parser.add_argument('-l','--program_location',
                        help='path to the inversion program',
                        type=str,default=r'$HOME/aniso1d/ai1oz_ak')    
    parser.add_argument('-r','--run_input',nargs=7,
                        help='command line input for the inversion program',
                        type=list,default=[1,0,0.1,40,1.05,1,0])    
    parser.add_argument('-ef','--errorfloor',
                        help='error floor for impedence tensor or resisitivity values',
                        type=float,default=0.1)
    parser.add_argument('-eft','--errorfloor_type',
                        help='type of error floor, absolute or relative',
                        type=str,default='relative')
    parser.add_argument('-wd','--working_directory',
                        help='working directory',
                        type=str,default='.')
    parser.add_argument('-el','--edifolder_list',
                        help='list of folders containing edi files to use, full path or relative to working directory',
                        type=str,default=None)
    parser.add_argument('-m','--mode',
                        help='mode to put in data file, impedence (I) or resistivity (R) and phase',
                        type=str,default='I')    
    parser.add_argument('-ps','--penalty_type_structure',
                        help='number describing type of structure penalty',
                        type=int,default=6)    
    parser.add_argument('-pa','--penalty_type_anisotropy',
                        help='number describing type of anisotropy penalty',
                        type=int,default=2)  
    parser.add_argument('-pws','--penalty_weight_structure',nargs='*',
                        help='structure penalty weights to apply in the inversion',
                        type=list,action='append',default=[1,10,100])
    parser.add_argument('-pwa','--penalty_weight_anisotropy',nargs='*',
                        help='anisotropy penalty weights to apply in the inversion',
                        type=list,action='append',default=[1,10,100])
    parser.add_argument('-imax','--iteration_max',
                        help='maximum number of iterations',
                        type=int,default=100)
    parser.add_argument('-i','--build_inmodel',
                        help='build inmodel, True or False',
                        type=bool,default=False)
    parser.add_argument('-ip','--inmodel_parameters_file',
                        help='full path (or path relative to working directory) to file containing inmodel parameters',
                        type=str)
    parser.add_argument('-id','--inmodel_modeldir',
                        help='full path to an output model file from previous run containing layer depths',
                        type=str)
    parser.add_argument('-s','--master_savepath',
                        help = 'master directory to save suite of runs into',
                        default = 'inversion_suite')
                        
    return parser.parse_args(arguments)


def create_inmodel_dictionary_from_file(input_file,
                                        x,y,
                                        working_directory = None):
    """
    update inmodel dictionary to get elevation details from file
    
    ------------------------------Parameters-----------------------------------    
    **input_file** full path to a csv file containing list of following parameters:
    elevation filename,offset,resmin,resmax,strike
    where:
    elevation filename = Full path to x y z file containing elevations of the 
                         constraining layer to put into the inversions, put
                         none if providing a constant elevation.
                         Numbers are converted to absolute values internally.
    offset = Constant depth of constraining layer, if provided in addition to
             elevation filename the offset is added/subtracted from depth 
             from file, positive down.
    resmin, resmax, strike = minimum and maximum resistivity values and strike 
                             of minimum resistivity for constraining layer
    **x** x position of station in same coordinate system as elevation file
    **y** y position of station in same coordinate system as elevation file
   
    """
 
    inmodel_dict = {}
    
    for line in open(input_file).readlines()[1:]:
        if str.lower(line[0]) != 'none':
            try:
                if working_directory is not None:
                    elevfn = os.path.join(line[0])
                else:
                    elevfn = line[0]
                elev = mted.get_elevation(x,y,elevfn)
            except IOError:
                print "File not found, set elevation to zero instead"
                elev = 0.0
        else:
            elev = 0.0
        params = [float(param) for param in line.strip().split(',')[1:]]
        inmodel_dict[round(elev+params[0],2)] = params[1:]

    return inmodel_dict
        

def create_filelist(wd,subfolder_list = None):
    """
    create a list of full paths to edi files    
    
    """
    
    edi_list = []    
    
    if subfolder_list is None:
        subfolder_list = [folder for folder, sf, f in os.walk(wd) if folder != wd]
        
    for subfolder in subfolder_list:
        epath = os.path.join(wd,subfolder)
        edi_list += [os.path.join(epath,ff) for ff in os.listdir(epath) if ff[-4:] == '.edi']
    
    return edi_list
    

def update_inputs():
    """
    update input parameters from command line
    
    """
    
    args = parse_arguments(argv)
    cline_inputs = {}
    cline_keys = [i for i in dir(args) if i[0] != '_']
    
    for key in cline_keys:
        cline_inputs[key] = getattr(args,key)

    return cline_inputs
    

def build_run():
    """
    build input files and run a suite of models
    runs one inversion per processor, make sure you have enough processors!
    
    """
    from mpi4py import MPI
    
    # get command line arguments as a dictionary
    input_parameters = update_inputs()
    
    # categorise inputs
    build_parameters = ['working_directory','datafile', 'errorfloor', 
                        'errorfloor_type', 'edipath', 'mode',
                        'penalty_type_structure', 'penalty_type_anisotropy',
                        'penalty_weight_structure', 'penalty_weight_anisotropy', 
                        'iteration_max','inmodel_dictionary']
    
    # establish the rank of the computer
    rank = MPI.COMM_WORLD.Get_rank()
    
    # make a master directory under the working directory to save all runs into
    master_directory = fh.make_unique_folder(input_parameters['master_savepath'])
    os.mkdir(master_directory)
    
    # create a list of edi files to model
    edi_list = create_filelist(os.path.join(input_parameters['working_directory'],
                                            input_parameters['edifolder_list']))
    
    # update input parameters for building of model
    build_inputs = {}
    for key in build_parameters:
        try:
            build_inputs[key] = input_parameters[key]
        except:
            pass

    # build a model
    Data = generate_inputfiles(edi_list[rank],build_inputs)
    os.chdir(Data.wd)
   
    # run the model
    call([input_parameters['program_location']]+[Data.datafile]+[str(n) for n in input_parameters['run_input']])


if __name__ == '__main__':
    build_run()
    