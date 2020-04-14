"""
  Run Programs for thermo param calculations
"""

import os
import subprocess
import shutil
import automol
import autofile
import thermp_io
from lib.runner import script
from lib.filesystem import orb as fsorb


# OBTAIN THE PATH TO THE DIRECTORY CONTAINING THE TEMPLATES #
CUR_PATH = os.path.dirname(os.path.realpath(__file__))


# MESSPF
def run_pf(pf_path, pf_script_str=script.MESSPF):
    """ run messpf
    """
    script.run_script(pf_script_str, pf_path)


# THERMP
def write_thermp_inp(spc_dct_i, thermp_file_name='thermp.dat'):
    """ write the thermp input file
    """
    ich = spc_dct_i['ich']
    h0form = spc_dct_i['Hfs'][0]
    formula = automol.inchi.formula(ich)

    # Write thermp input file
    enthalpyt = 0.
    breakt = 1000.
    thermp_str = thermp_io.writer.thermp_input(
        formula=formula,
        delta_h=h0form,
        enthalpy_temp=enthalpyt,
        break_temp=breakt,
        thermp_file_name=thermp_file_name)

    # Write the file
    with open(thermp_file_name, 'w') as thermp_file:
        thermp_file.write(thermp_str)


def run_thermp(pf_path, thermp_path,
               thermp_file_name='thermp.dat', pf_file_name='pf.dat'):
    """
    Runs thermp.exe
    Requires thermp input file to be present
    partition function (pf) output file and
    """

    # Set full paths to files
    thermp_file = os.path.join(thermp_path, thermp_file_name)
    pf_outfile = os.path.join(pf_path, pf_file_name)

    # Copy MESSPF output file to THERMP run dir and rename to pf.dat
    pf_datfile = os.path.join(thermp_path, 'pf.dat')
    shutil.copyfile(pf_outfile, pf_datfile)

    # Check for the existance of ThermP input and PF output
    assert os.path.exists(thermp_file)
    assert os.path.exists(pf_outfile)

    # Run thermp
    subprocess.check_call(['thermp', thermp_file])

    # Read ene from file
    with open('thermp.out', 'r') as thermfile:
        lines = thermfile.readlines()
    line = lines[-1]
    hf298k = line.split()[-1]
    return hf298k


# PAC99
def run_pac(spc_dct_i, nasa_path):
    """ 
    Run pac99 for a given species name (formula)
    https://www.grc.nasa.gov/WWW/CEAWeb/readme_pac99.htm
    requires formula+'i97' and new.groups files
    """
    ich = spc_dct_i['ich']
    formula = automol.inchi.formula(ich)

    # Run pac99
    # Set file names for pac99
    i97_file = os.path.join(nasa_path, formula + '.i97')
    newgroups_file = os.path.join(nasa_path, 'new.groups')
    newgroups_ref = os.path.join(CUR_PATH, 'new.groups')

    # Copy new.groups file from thermo src dir to run dir
    shutil.copyfile(newgroups_ref, newgroups_file)

    # Check for the existance of pac99 files
    assert os.path.exists(i97_file)
    assert os.path.exists(newgroups_file)

    # Run pac99
    proc = subprocess.Popen('pac99', stdin=subprocess.PIPE)
    proc.communicate(bytes(formula, 'utf-8'))

    # Read the pac99 polynomial
    with open(os.path.join(nasa_path, formula+'.c97'), 'r') as pac99_file:
        pac99_str = pac99_file.read()
    pac99_poly_str = thermo.nasapoly.get_pac99_polynomial(pac99_str)

    return pac99_poly_str


# PATH CONTROL
def get_starting_path():
    """ get original working directory
    """
    starting_path = os.getcwd()
    return starting_path


def go_to_path(path):
    """ change directory to path and return the original working directory
    """
    os.chdir(path)


def return_to_path(path):
    """ change directory to starting path
    """
    os.chdir(path)


def prepare_path(path, loc):
    """ change directory to starting path, return chemkin path
    """
    new_path = os.path.join(path, loc)
    return new_path


def get_thermo_paths(spc_save_path, spc_info, har_level):
    """ set up the path for saving the pf input and output
    currently using the harmonic theory directory for this because
    there is no obvious place to save this information for a random
    assortment of har_level, tors_level, vpt2_level
    """
    orb_restr = fsorb.orbital_restriction(
        spc_info, har_level)
    har_levelp = har_level[1:3]
    har_levelp.append(orb_restr)

    thy_save_fs = autofile.fs.theory(spc_save_path)
    thy_save_fs[-1].create(har_levelp)
    thy_save_path = thy_save_fs[-1].path(har_levelp)
    bld_locs = ['PF', 0]
    bld_save_fs = autofile.fs.build(thy_save_path)
    bld_save_fs[-1].create(bld_locs)
    pf_path = bld_save_fs[-1].path(bld_locs)

    # prepare NASA polynomials
    bld_locs = ['NASA_POLY', 0]
    bld_save_fs[-1].create(bld_locs)
    nasa_path = bld_save_fs[-1].path(bld_locs)

    print('Build Path for Partition Functions')
    print(pf_path)

    return pf_path, nasa_path