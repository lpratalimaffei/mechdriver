""" determine the reaction type by calling the autochem code
"""

import automol
from phydat import phycon
from lib import filesys
from lib.reaction import grid as rxngrid


def ts_class(rct_zmas, prd_zmas, rad_rad, ts_mul, low_mul, high_mul,
             rct_cnf_save_fs_lst, prd_cnf_save_fs_lst, given_class):
    """ Determine type of reaction and related ts info from the
        reactant and product z-matrices.
        Returns the type, the transition state z-matrix, the name of the
        coordinate to optimize, the grid of values for the initial grid search,
        the torsion names and symmetries, and whether or not to update the
        guess on successive steps.
        These parameters are set for both the initial and a backup
        evaluation for if the initial ts search fails.
    """

    # Convert termolecular reactions to bimolecular reactions
    rct_tors_names = []
    if len(rct_zmas) > 2 or len(prd_zmas) > 2:
        rct_zmas, prd_zmas, rct_tors_names = conv_termol_to_bimol(
            rct_zmas, prd_zmas)

    # Determine the reaction types
    #for rct_zma in rct_zmas:
        # print('zma test in ts_class:', automol.zmatrix.string(rct_zma))
    #for prd_zma in prd_zmas:
        # print('zma test in ts_class:', automol.zmatrix.string(prd_zma))
    ret = determine_reaction_type(
        rct_zmas, prd_zmas,
        ts_mul, high_mul, low_mul,
        rct_cnf_save_fs_lst, prd_cnf_save_fs_lst,
        rct_tors_names,
        given_class, rad_rad)
    [typ, bkp_typ,
     ts_zma, bkp_ts_zma,
     tors_names, bkp_tors_names, const_tors_names, const_angs_names,
     dist_name, bkp_dist_name, brk_name,
     frm_bnd_keys, brk_bnd_key, const_bnd_key, rcts_gra, rxn_dir] = ret

    # Determine grid for preliminary search for all different reaction types
    dist_coo, = automol.zmatrix.coordinates(ts_zma)[dist_name]
    syms = automol.zmatrix.symbols(ts_zma)
    # print('dist_coo', dist_coo)
    ts_bnd_len = tuple(sorted(map(syms.__getitem__, dist_coo)))
    grid, update_guess, bkp_grid, bkp_update_guess = rxngrid.build_grid(
        typ, bkp_typ, ts_bnd_len, ts_zma, dist_name, brk_name, npoints=None)

    # Hack in variational grids for addition and abstraction
    if 'addition' in typ and 'rad' not in typ:
        var_grid, _ = rxngrid.radrad_addition_grid()
    elif 'hydrogen abstraction' in typ and 'rad' in typ:
        var_grid, _ = rxngrid.radrad_hydrogen_abstraction_grid()
    else:
        var_grid = []
    # print('var grid', var_grid)

    # Build class data lists to return from the function
    if typ:
        ts_class_data = [
            ts_zma, dist_name, brk_name,
            grid, frm_bnd_keys, brk_bnd_key, const_bnd_key,
            tors_names, const_tors_names, const_angs_names, update_guess, var_grid, rcts_gra, rxn_dir]
    else:
        ts_class_data = []
    if bkp_typ:
        bkp_ts_class_data = [
            bkp_typ, bkp_ts_zma, bkp_dist_name,
            bkp_grid, bkp_tors_names, bkp_update_guess]
    else:
        bkp_ts_class_data = []

    return typ, ts_class_data, bkp_ts_class_data


def conv_termol_to_bimol(rct_zmas, prd_zmas):
    """ Convert termolecular reaction to a bimolecular reaction
    """
    # Force a trimolecular reaction to behave like a bimolecular.
    # Termolecular spc often arise from the direct decomp of some init product.
    # Need to be able to find the TS for channel preceding direct decomp.
    rct_tors_names = []
    if len(rct_zmas) > 2:
        ret = automol.zmatrix.ts.addition(rct_zmas[1:-1], [prd_zmas[-1]])
        new_zma, dist_name, rct_tors_names = ret
        new_zma = automol.zmatrix.standard_form(new_zma)
        babs2 = automol.zmatrix.get_babs2(new_zma, dist_name)
        new_zma = automol.zmatrix.set_values(
            new_zma, {dist_name: 2.2, babs2: 180. * phycon.DEG2RAD})
        rct_zmas = [rct_zmas[0], new_zma]
    elif len(prd_zmas) > 2:
        ret = automol.zmatrix.ts.addition(prd_zmas[1:-1], [prd_zmas[-1]])
        new_zma, dist_name, rct_tors_names = ret
        new_zma = automol.zmatrix.standard_form(new_zma)
        babs1 = automol.zmatrix.get_babs1(new_zma, dist_name)
        aabs1 = babs1.replace('D', 'A')
        new_zma = automol.zmatrix.set_values(
            new_zma, {dist_name: 2.2, aabs1: 170. * phycon.DEG2RAD})
        prd_zmas = [prd_zmas[0], new_zma]

    return rct_zmas, prd_zmas, rct_tors_names


def determine_reaction_type(rct_zmas, prd_zmas,
                            ts_mul, high_mul, low_mul,
                            rct_cnf_save_fs_lst, prd_cnf_save_fs_lst,
                            rct_tors_names,
                            given_class, rad_rad):
    """ Determine forward-reverse reaction for given rcts and prds
    """
    typ = None
    bkp_typ = ''
    bkp_ts_zma = ()
    bkp_tors_names = []
    bkp_dist_name = []
    dist_name = []
    brk_name = []
    const_angs_names = []
    const_tors_names = []
    frm_bnd_keys = frozenset({})
    brk_bnd_key = frozenset({})
    const_bnd_key = frozenset({})
    rcts_gra = ()
    rxn_dir = 'forward'

    # Cycle through each possible reaction type checking if it is in the class
    # Check both orders of reactants and products
    for direction in ('forward', 'reverse'):

        # Set cnf filesystem and flip reactants and products for second check
        if direction == 'forward':
            cnf_save_fs_lst = rct_cnf_save_fs_lst
        elif direction == 'reverse':
            zmas = [rct_zmas, prd_zmas]
            rct_zmas, prd_zmas = zmas[1], zmas[0]
            cnf_save_fs_lst = prd_cnf_save_fs_lst

        # Check for addition
        ret = automol.zmatrix.ts.addition(rct_zmas, prd_zmas, rct_tors_names)
        if ret and (not given_class or given_class == 'addition'):
            typ = 'addition'
            ts_zma, dist_name, frm_bnd_keys, tors_names, rcts_gra = ret
            typ += ' '
            typ += set_ts_spin(ts_mul, high_mul, low_mul)
            # Set up beta sci as fall back option for failed addn TS search
            ret2 = automol.zmatrix.ts.beta_scission(rct_zmas, prd_zmas)
            if ret2:
                bkp_typ = 'beta scission'
                bkp_ts_zma, bkp_dist_name, _, bkp_tors_names, _ = ret2

        # Check for beta-scission
        if typ is None:
            ret = automol.zmatrix.ts.beta_scission(rct_zmas, prd_zmas)
            if ret and (not given_class or given_class == 'betascission'):
                typ = 'beta scission'
                ts_zma, dist_name, brk_bnd_key, tors_names, rcts_gra = ret
                ret2 = automol.zmatrix.ts.addition(
                    prd_zmas, rct_zmas, rct_tors_names)
                if ret2:
                    bkp_typ = 'addition'
                    bkp_ts_zma, bkp_dist_name, _, bkp_tors_names, _ = ret2

        # Check for hydrogen migration
        if typ is None:
            orig_dist = automol.zmatrix.ts.min_hyd_mig_dist(rct_zmas, prd_zmas)
            hmcls = not given_class or given_class == 'hydrogenmigration'
            if orig_dist and hmcls:
                rct_zmas = filesys.mincnf.min_dist_conformer_zma_geo(
                    orig_dist, cnf_save_fs_lst[0])
                # print('rct_zmas in hydrogen_migration:', rct_zmas)
                ret = automol.zmatrix.ts.hydrogen_migration(rct_zmas, prd_zmas)
                if ret:
                    typ = 'hydrogen migration'
                    zma, dist_name, frm_bnd_keys, brk_bnd_key, const_bnd_key, tors_names, rcts_gra = ret
                    ts_zma = zma

        # Check for hydrogen abstraction
        if typ is None:
            ret = automol.zmatrix.ts.hydrogen_abstraction(
                rct_zmas, prd_zmas, sigma=False)
            hmcls = not given_class or given_class == 'hydrogenmigration'
            if ret and hmcls:
                typ = 'hydrogen abstraction'
                ts_zma, dist_name, frm_bnd_keys, brk_bnd_key, tors_names, rcts_gra = ret
                typ += ' '
                typ += set_ts_spin(ts_mul, high_mul, low_mul)

        # Need cases for
        # (i) hydrogen abstraction where the radical is a sigma radical
        # (ii) for abstraction of a heavy atom rather than a hydrogen atom.

        # Check for insertion
        if typ is None:
            ret = automol.zmatrix.ts.insertion(rct_zmas, prd_zmas)
            if ret and (not given_class or given_class == 'insertion'):
                typ = 'insertion'
                ts_zma, dist_name, tors_names = ret
                typ += ' '
                typ += set_ts_spin(ts_mul, high_mul, low_mul)

        # Check for subsitution
        # if typ is None:
        #     ret = automol.zmatrix.ts.substitution(rct_zmas, prd_zmas)
        #     if ret and (not given_class or given_class == 'substitution'):
        #         typ = 'substitution'
        #         ts_zma, dist_name, tors_names = ret
        #         typ += ' '
        #         typ += set_ts_spin(ts_mul, high_mul, low_mul)

        # Check for elimination
        if typ is None:
            orig_dist = automol.zmatrix.ts.min_unimolecular_elimination_dist(
                rct_zmas, prd_zmas)
            # print('origdist', orig_dist)
            if orig_dist:
                rct_zmas = filesys.mincnf.min_dist_conformer_zma_geo(
                    orig_dist, cnf_save_fs_lst[0])
                ret = automol.zmatrix.ts.concerted_unimolecular_elimination(
                    rct_zmas, prd_zmas)
                if ret and (not given_class or given_class == 'elimination'):
                    typ = 'elimination'
                    ts_zma, dist_name, brk_name, brk_bnd_keys, frm_bnd_keys, tors_names, rcts_gra = ret
                    typ += ' '
                    typ += set_ts_spin(ts_mul, high_mul, low_mul)

        # Check for ring forming scission
        if typ is None:
            ret = automol.zmatrix.ts.ring_forming_scission(rct_zmas, prd_zmas)
            if ret and (not given_class or given_class == 'ring forming scission'):
                typ = 'ring forming scission'
                # ts_zma, dist_name, brk_name, brk_bnd_key, frm_bnd_keys, tors_names, rcts_gra = ret
                ts_zma, dist_name, brk_bnd_key, const_tors_names, tors_names, const_angs_names, rcts_gra = ret
                typ += ' '
                typ += set_ts_spin(ts_mul, high_mul, low_mul)

        # Break if reaction found
        if typ is not None:
            break
        else:
            rxn_dir = 'reverse'
            print("Reaction has been reversed by reaction classifier.")

    # Nothing was found
    if typ is None:
        print("Failed to classify reaction.")
        return [], []

    # set up back up options for any radical radical case
    if rad_rad:
        typ = 'radical radical ' + typ
    if bkp_typ:
        if rad_rad:
            bkp_typ = 'radical radical ' + bkp_typ

    # print('brk_bnd_key test:', brk_bnd_key)
    # print('ts_zma test:\n',automol.zmatrix.string(ts_zma))
    if not brk_name:
        if brk_bnd_key:
            brk_name = automol.zmatrix.bond_key_from_idxs(ts_zma, brk_bnd_key)
        else:
            brk_name = []

    # Set big list to return stuff
    ret = [
        typ, bkp_typ,
        ts_zma, bkp_ts_zma,
        tors_names, bkp_tors_names, const_tors_names, const_angs_names,
        dist_name, bkp_dist_name, brk_name,
        frm_bnd_keys, brk_bnd_key, const_bnd_key, rcts_gra, rxn_dir]

    return ret


def set_rxn_molecularity(rct_zmas, prd_zmas):
    """ Determine molecularity of the reaction
    """
    rct_molecularity = automol.zmatrix.count(rct_zmas)
    prd_molecularity = automol.zmatrix.count(prd_zmas)
    rxn_molecularity = (rct_molecularity, prd_molecularity)
    return rxn_molecularity


def set_ts_spin(ts_mul, high_mul, low_mul):
    """ Determine if reaction is on the high-spin or low-spin surface
    """
    if ts_mul == high_mul:
        spin = 'high'
    elif ts_mul == low_mul:
        spin = 'low'
    return spin


def determine_rad_rad(rxn_muls):
    """ determine if reaction is radical-radical
    """
    rct_muls = rxn_muls[0]
    if len(rct_muls) > 1:
        mul1, mul2 = rct_muls
        rad_rad = bool(mul1 > 1 and mul2 > 1)
    else:
        prd_muls = rxn_muls[1]
        if len(prd_muls) > 1:
            mul1, mul2 = prd_muls
            rad_rad = bool(mul1 > 1 and mul2 > 1)
        else:
            rad_rad = False
    return rad_rad
