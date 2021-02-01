""" es_runners for coordinate scans
"""

import automol
from mechroutines.es.runner import scan
from mechlib import filesys
from mechlib.structure import tors as torsprep
from mechlib.amech_io import printer as ioprinter
from mechlib import structure


def hindered_rotor_scans(
        zma, spc_info, mod_thy_info, thy_save_fs,
        zma_run_path, zma_save_path,
        torsions, tors_model,
        script_str, overwrite,
        saddle=False, const_names=None,
        retryfail=True, chkstab=None, **opt_kwargs):
    """ Perform scans over each of the torsional coordinates
    """

    run_tors_names = automol.rotor.names(torsions)
    run_tors_grids = automol.rotor.grids(torsions)

    print('tors info')
    print(run_tors_names)
    print(run_tors_grids)

    # Set constraints
    const_names = structure.tors.set_constraint_names(
        zma, run_tors_names, tors_model)

    # Set if scan is rigid or relaxed
    scn_typ = 'relaxed' if tors_model != '1dhrfa' else 'rigid'

    # Set appropriate value for check stability
    # If not set, don't check if saddle=True
    if chkstab is None:
        chkstab = bool(not saddle)

    ioprinter.run_rotors(run_tors_names, const_names)

    # for tors_name, tors_grid in zip(tors_names, tors_grids):
    for tors_names, tors_grids in zip(run_tors_names, run_tors_grids):

        ioprinter.info_message(
            'Running Rotor: {}...'.format(tors_names),
            newline=1)

        # Setting the constraints
        constraint_dct = torsprep.build_constraint_dct(
            zma, const_names, tors_names)

        # Setting the filesystem
        # print('hr constraint dct', constraint_dct)
        scn_run_fs = filesys.build.scn_fs_from_cnf(
            zma_run_path, constraint_dct=constraint_dct)
        scn_save_fs = filesys.build.scn_fs_from_cnf(
            zma_save_path, constraint_dct=constraint_dct)

        scan.execute_scan(
            zma=zma,
            spc_info=spc_info,
            mod_thy_info=mod_thy_info,
            thy_save_fs=thy_save_fs,
            coord_names=tors_names,
            coord_grids=tors_grids,
            scn_run_fs=scn_run_fs,
            scn_save_fs=scn_save_fs,
            scn_typ=scn_typ,
            script_str=script_str,
            overwrite=overwrite,
            update_guess=True,
            reverse_sweep=True,
            saddle=False,
            constraint_dct=constraint_dct,
            retryfail=retryfail,
            chkstab=False,
            **opt_kwargs,
        )
