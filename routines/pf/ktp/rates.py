"""
Write and Read MESS files for Rates
"""

import importlib
import copy
import ioformat
import automol
import mess_io
from mess_io.writer import rxnchan_header_str
from routines.pf.models import blocks
from routines.pf.models import build
from routines.pf.models.ene import set_reference_ene
from routines.pf.models.ene import calc_channel_enes
from routines.pf.models import etrans
from routines.pf.models import tunnel
from routines.pf.models.inf import set_pf_info
from routines.pf.models.inf import set_ts_cls_info
from routines.pf.models.inf import make_rxn_str
from routines.pf.models.typ import treat_tunnel
from routines.pf.models.typ import need_fake_wells


BLOCK_MODULE = importlib.import_module('routines.pf.models.blocks')


# Input string writer
def make_messrate_str(globkey_str, energy_trans_str, rxn_chan_str):
    """ Combine various MESS strings together to combined MESS rates
    """
    return mess_io.writer.messrates_inp_str(
        globkey_str, energy_trans_str, rxn_chan_str)


# Headers
def make_header_str(temps, press):
    """ makes the standard header and energy transfer sections for MESS input file
    """

    print('\nPreparing global keywords section for MESS input...')

    print(' - Using temperatures and pressures defined by user')
    print(' - Using internal AutoMech defaults for other MESS keywords:')
    keystr1 = (
        'EnergyStepOverTemperature, ExcessEnergyOverTemperature, ' +
        'ModelEnergyLimit'
    )
    keystr2 = (
        'CalculationMethod, WellCutoff, WellExtension, ' +
        'ChemicalEigenvalueMax, ReductionMethod, AtomDistanceMin'
    )
    print('     {}'.format(keystr1))
    print('     {}'.format(keystr2))

    header_str = mess_io.writer.global_reaction(
        temps, press, excess_ene_temp=None, well_extend=None)

    return header_str


def make_global_etrans_str(rxn_lst, spc_dct, etrans_dct):
    """ Makes the standard header and energy transfer sections
        for MESS input file
    """

    print('\nPreparing energy transfer section for MESS input...')

    # Determine the species for which you
    print('\n- Determining reference well species...')
    well_info = etrans.set_etrans_well(rxn_lst, spc_dct)

    # Determine the bath
    print('\n- Determining information for the bath species...')
    bath_info = etrans.set_bath(spc_dct, etrans_dct)

    # Write the MESS energy transfer strings
    edown_str, collid_str = etrans.make_energy_transfer_strs(
        well_info, bath_info, etrans_dct)
    energy_trans_str = mess_io.writer.global_energy_transfer(
        edown_str, collid_str)

    return energy_trans_str


# Reaction Channel Writers for the PES
def make_pes_mess_str(spc_dct, rxn_lst, pes_idx,
                      run_prefix, save_prefix, label_dct,
                      model_dct, thy_dct):
    """ Write all the MESS input file strings for the reaction channels
    """

    print('\nPreparing reaction channel section for MESS input... ')

    # Initialize empty MESS strings
    full_well_str, full_bi_str, full_ts_str = '', '', ''
    full_dat_str_dct = {}
    pes_ene_dct = {}
    conn_lst = tuple()

    # Set the energy and model for the first reference species
    # print('\nCalculating reference energy for PES')

    ref_ene, ref_model = set_reference_ene(
        rxn_lst, spc_dct, thy_dct, model_dct,
        run_prefix, save_prefix, ref_idx=0)
    # Loop over all the channels and write the MESS strings
    written_labels = []
    basis_energy_dct = {}
    for rxn in rxn_lst:

        print('\n\nReading PES electronic structure data ' +
              'from save filesystem for')
        print('Channel {}: {} = {}...'.format(
            rxn['chn_idx'],
            '+'.join(rxn['reacs']),
            '+'.join(rxn['prods'])))

        # Set the TS name and channel model
        tsname = 'ts_{:g}_{:g}'.format(pes_idx, rxn['chn_idx'])
        chn_model = rxn['model'][1]

        # Obtain useful info objects
        pf_info = set_pf_info(model_dct, thy_dct, chn_model, ref_model)
        ts_cls_info = set_ts_cls_info(spc_dct, model_dct, tsname, chn_model)

        # Obtain all of the species data
        if not chn_model in basis_energy_dct:
            basis_energy_dct[chn_model] = {}

        chnl_infs, chn_basis_ene_dct = get_channel_data(rxn, tsname, spc_dct,
                                     basis_energy_dct[chn_model],
                                     pf_info, ts_cls_info,
                                     run_prefix, save_prefix)

        basis_energy_dct[chn_model].update(chn_basis_ene_dct)

        # Calculate the relative energies of all spc on the channel
        chnl_enes = calc_channel_enes(chnl_infs, ref_ene,
                                      chn_model, ref_model)

        # Write the mess strings for all spc on the channel
        mess_strs, dat_str_dct, written_labels = _make_channel_mess_strs(
            tsname, rxn, spc_dct, label_dct, written_labels,
            chnl_infs, chnl_enes, ts_cls_info)

        # Append to full MESS strings
        [well_str, bi_str, ts_str] = mess_strs
        full_well_str += well_str
        full_bi_str += bi_str
        full_ts_str += ts_str
        full_dat_str_dct.update(dat_str_dct)

        print('rxn', rxn)
        print('enes', chnl_enes)
        print('label dct', label_dct)
        print('written labels', written_labels)

        # Build PES energy dct and connection lists
        #for side, ene in chnl_enes.items():
        #    if 'fake' not in side:
        #        if side in ('reacs', 'prods'):
        #            rct_str = '+'.join(rxn[side])
        #            label = label_dct[rct_str]
        #            pes_ene_dct[label] = ene        
        #        elif 'ts' in side:
        #            rct_str = tsname
        #            label = label_dct[rct_str]
        #            pes_ene_dct[label] = max(ene)

        #reac_str = '+'.join(rxn['reacs'])
        #prod_str = '+'.join(rxn['prods'])
        #reac_lbl = label_dct[reac_str]
        #prod_lbl = label_dct[prod_str]
        #ts_lbl = label_dct[tsname]
        #conn_lst += ((reac_lbl, ts_lbl), (ts_lbl, prod_lbl))

    # Combine all the reaction channel strings
    rxn_chan_str = '\n'.join([full_well_str, full_bi_str, full_ts_str])

    return rxn_chan_str, full_dat_str_dct, pes_ene_dct, conn_lst


def _make_channel_mess_strs(tsname, rxn, spc_dct, label_dct, written_labels,
                            chnl_infs, chnl_enes, ts_cls_info):
    """ make the partition function strings for each of the channels
    includes strings for each of the unimolecular wells, bimolecular fragments,
    and transition states connecting them.
    It also includes a special treatment for abstraction to include phase space
    blocks and coupling bimolecular fragments to fake van der Waals wells
    """

    # Initialize empty strings
    bi_str, well_str, ts_str = '', '', ''
    full_dat_dct = {}

    # Write the MESS string for the channel reactant(s) and product(s)
    for side in ('reacs', 'prods'):

        # Get information from relevant dictionaries
        rgt_names = rxn[side]
        rgt_infs = chnl_infs[side]
        rgt_ene = chnl_enes[side]

        # Build the species string for reactant(s)/product(s)
        # Skip molec string building for termolecular species (may need agn)
        spc_strs = []
        if len(rgt_names) < 3:
            for inf in rgt_infs:
                spc_str, dat_dct = _make_spc_mess_str(inf)
                spc_strs.append(spc_str)
                full_dat_dct.update(dat_dct)

        # Set the labels to put into the file
        spc_label = [automol.inchi.smiles(spc_dct[name]['inchi'])
                     for name in rgt_names]
        _rxn_str = make_rxn_str(rgt_names)
        _rxn_str_rev = make_rxn_str(rgt_names[::-1])
        if _rxn_str in label_dct:
            chn_label = label_dct[_rxn_str]
        elif _rxn_str_rev in label_dct:
            chn_label = label_dct[_rxn_str_rev]
        else:
            print('no {} in label dct'.format(_rxn_str))

        # Write the strings
        if chn_label not in written_labels:
            written_labels.append(chn_label)
            if len(rgt_names) == 3:
                bi_str += '\n! {} + {} + {}\n'.format(
                    rgt_names[0], rgt_names[1], rgt_names[2])
                bi_str += mess_io.writer.dummy(chn_label, zero_ene=rgt_ene)
                # bi_str += '\n! DUMMY FOR UNSTABLE SPECIES\n'
                # bi_str += mess_io.writer.dummy(chn_label, zero_ene=None)
            elif len(rgt_names) == 2:
                # bi_str += mess_io.writer.species_separation_str()
                bi_str += '\n! {} + {}\n'.format(rgt_names[0], rgt_names[1])
                bi_str += mess_io.writer.bimolecular(
                    chn_label, spc_label[0], spc_strs[0],
                    spc_label[1], spc_strs[1], rgt_ene)
            else:
                edown_str = rgt_infs[0].get('edown_str', None)
                collid_freq_str = rgt_infs[0].get('collid_freq_str', None)

                # well_str += mess_io.writer.species_separation_str()
                well_str += '\n! {}\n'.format(rgt_names[0])
                well_str += mess_io.writer.well(
                    chn_label, spc_strs[0],
                    zero_energy=rgt_ene,
                    edown_str=edown_str,
                    collid_freq_str=collid_freq_str)

        # Initialize the reactant and product MESS label
        if side == 'reacs':
            reac_label = chn_label
            inner_reac_label = chn_label
        else:
            prod_label = chn_label
            inner_prod_label = chn_label

    # For abstractions: Write MESS strings for fake reac and prod wells and TS
    if chnl_infs.get('fake_vdwr', None) is not None:

        # Write all the MESS Strings for Fake Wells and TSs
        fwell_str, fts_str, fake_lbl, fake_dct = _make_fake_mess_strs(
            rxn, 'reacs', chnl_infs['fake_vdwr'],
            chnl_enes, label_dct, reac_label)

        # Append the fake strings to overall strings
        well_str += fwell_str
        ts_str += fts_str

        # Re-set the reactant label for the inner transition state
        inner_reac_label = fake_lbl

        # Update the data string dct if necessary
        full_dat_dct.update(fake_dct)

    if chnl_infs.get('fake_vdwp', None) is not None:

        # Write all the MESS Strings for Fake Wells and TSs
        fwell_str, fts_str, fake_lbl, fake_dct = _make_fake_mess_strs(
            rxn, 'prods', chnl_infs['fake_vdwp'],
            chnl_enes, label_dct, prod_label)

        # Append the fake strings to overall strings
        well_str += fwell_str
        ts_str += fts_str

        # Reset the product labels for the inner transition state
        inner_prod_label = fake_lbl

        # Update the data string dct if necessary
        full_dat_dct.update(fake_dct)

    # Write MESS string for the inner transition state; append full
    ts_label = label_dct[tsname]
    sts_str, ts_dat_dct = _make_ts_mess_str(
        chnl_infs, chnl_enes, ts_cls_info,
        ts_label, inner_reac_label, inner_prod_label)
    ts_str += sts_str
    full_dat_dct.update(ts_dat_dct)

    return [well_str, bi_str, ts_str], full_dat_dct, written_labels


def _make_spc_mess_str(inf_dct):
    """ makes the main part of the MESS species block for a given species
    """
    mess_writer = getattr(BLOCK_MODULE, inf_dct['writer'])
    return mess_writer(inf_dct)


def _make_ts_mess_str(chnl_infs, chnl_enes, ts_cls_info,
                      ts_label, inner_reac_label, inner_prod_label):
    """ makes the main part of the MESS species block for a given species
    """

    # Unpack info objects
    [_, ts_sadpt, ts_nobarrier, tunnel_model, radrad] = ts_cls_info

    # Initialize data string objects
    ts_dat_dct = {}
    flux_str, sct_str = '', ''
    flux_dat_name = 'flux.dat'
    sct_dat_name = 'sct.dat'

    # Write the initial data string and dat str dct with mdhr str
    mess_writer = getattr(BLOCK_MODULE, chnl_infs['ts']['writer'])
    if chnl_infs['ts']['writer'] == 'species_block':
        mess_str, mdhr_dat = mess_writer(chnl_infs['ts'])
    elif chnl_infs['ts']['writer'] == 'pst_block':
        if len(chnl_infs['reacs']) == 2:
            mess_str, mdhr_dat = mess_writer(
                chnl_infs['ts'], *chnl_infs['reacs'])
        else:
            mess_str, mdhr_dat = mess_writer(
                chnl_infs['ts'], *chnl_infs['prods'])
    # elif chnl_infs['ts']['writer'] == 'pst_block':
        # mess_str, mdhr_dat = mess_writer(chnl_infs['ts'], *chnl_infs['reacs'])
    elif chnl_infs['ts']['writer'] == 'vrctst_block':
        mess_str, mdhr_dat = mess_writer(
            chnl_infs['ts'], *chnl_infs['reacs'])
    elif chnl_infs['ts']['writer'] == 'rpvtst_block':
        mess_str = mess_writer(chnl_infs['ts'], *chnl_infs['reacs'])
        mdhr_dat = {}

    # Write the appropriate string for the tunneling model
    tunnel_str, sct_str = '', ''
    if treat_tunnel(tunnel_model, ts_sadpt, ts_nobarrier, radrad):
        if tunnel_model == 'eckart':
            ts_idx = chnl_infs['ts'].get('ts_idx', 0)
            symm_barrier = chnl_infs['ts'].get('symm_barrier', False)
            tunnel_str = tunnel.write_mess_eckart_str(
                chnl_enes, chnl_infs['ts']['imag'],
                ts_idx=ts_idx, symm_barrier=symm_barrier)
        # elif tun_model == 'sct':
        #     tunnel_file = tsname + '_sct.dat'
        #     path = 'cat'
        #     tunnel_str, sct_str = tunnel.write_mess_sct_str(
        #         spc_dct[tsname], pf_levels, path,
        #         imag, tunnel_file,
        #         cutoff_energy=2500, coord_proj='cartesian')
    else:
        pass

    # Write the MESS string for the TS
    write_ts_pt_str = bool(
        (not radrad and ts_sadpt != 'rpvtst') or
        (radrad and ts_nobarrier != 'rpvtst')
    )
    if write_ts_pt_str:
        ts_ene = chnl_enes['ts'][0]
        ts_str = '\n' + mess_io.writer.ts_sadpt(
            ts_label, inner_reac_label, inner_prod_label,
            mess_str, ts_ene, tunnel_str)
    else:
        ts_enes = chnl_enes['ts']
        ts_str = '\n' + mess_io.writer.ts_variational(
            ts_label, inner_reac_label, inner_prod_label,
            mess_str, ts_enes, tunnel_str)

    # Place strings in data dct if they are not empty
    if mdhr_dat:
        ts_dat_dct.update(mdhr_dat)
    if flux_str:
        ts_dat_dct.update({flux_dat_name: flux_str})
    if sct_str:
        ts_dat_dct.update({sct_dat_name: sct_str})

    return ts_str, ts_dat_dct


def _make_fake_mess_strs(rxn, side, fake_inf_dcts,
                         chnl_enes, label_dct, side_label):
    """ write the MESS strings for the fake wells and TSs
    """

    # Set vars based on the reacs/prods
    if side == 'reacs':
        well_key = 'fake_vdwr'
        ts_key = 'fake_vdwr_ts'
        prepend_key = 'FRB'
    elif side == 'prods':
        well_key = 'fake_vdwp'
        ts_key = 'fake_vdwp_ts'
        if rxn['reacs'] == rxn['prods'] or rxn['reacs'] == rxn['prods'][::-1]: 
           prepend_key = 'FRB'
        else:   
           prepend_key = 'FPB'

    # Initialize well and ts strs and data dcts
    fake_dat_dct = {}
    well_str, ts_str = '', ''

    # Build a fake TS dct
    ts_inf_dct = {
        'n_pst': 6.0,
        'cn_pst': 10.0
    }

    # MESS string for the fake reactant side well
    well_dct_key = make_rxn_str(rxn[side], prepend='F')
    well_dct_key_rev = make_rxn_str(rxn[side][::-1], prepend='F')
    if well_dct_key in label_dct:
        fake_well_label = label_dct[well_dct_key]
    elif well_dct_key_rev in label_dct:
        fake_well_label = label_dct[well_dct_key_rev]
    else:    
        print('No label {} in label dict'.format(well_dct_key))
    # well_str += mess_io.writer.species_separation_str()
    well_str += '\n! Fake Well for {}\n'.format(
        '+'.join(rxn[side]))
    fake_well, well_dat = blocks.fake_species_block(*fake_inf_dcts)
    well_str += mess_io.writer.well(
        fake_well_label, fake_well, chnl_enes[well_key])

    # MESS PST TS string for fake reactant side well -> reacs
    pst_dct_key = make_rxn_str(rxn[side], prepend=prepend_key)
    pst_dct_key_rev = make_rxn_str(rxn[side][::-1], prepend=prepend_key)
    if pst_dct_key in label_dct:
        pst_label = label_dct[pst_dct_key]
    elif pst_dct_key_rev in label_dct:
        pst_label = label_dct[pst_dct_key_rev]
    else:    
        print('No label {} in label dict'.format(pst_dct_key))
    pst_ts_str, pst_ts_dat = blocks.pst_block(ts_inf_dct, *fake_inf_dcts)
    ts_str += '\n' + mess_io.writer.ts_sadpt(
        pst_label, side_label, fake_well_label, pst_ts_str,
        chnl_enes[ts_key], tunnel='')

    # Build the data dct
    if well_dat:
        fake_dat_dct.update(well_dat)
    if pst_ts_dat:
        fake_dat_dct.update(pst_ts_dat)

    return well_str, ts_str, fake_well_label, fake_dat_dct


# Data Retriever Functions
def get_channel_data(rxn, tsname, spc_dct, model_basis_energy_dct, pf_info, ts_cls_info,
                     run_prefix, save_prefix):
    """ generate dcts with the models
    """

    # Unpack info objects
    [chn_pf_levels, chn_pf_models, ref_pf_levels, ref_pf_models] = pf_info
    [ts_class, ts_sadpt, ts_nobarrier, _, _] = ts_cls_info

    # Initialize the dict
    chnl_infs = {}

    # Initialize the symm_barrier variable for TS
    symm_barrier = False

    # Determine the MESS data for the reactants and products
    # Gather data or set fake information for dummy reactants/products
    chnl_infs['reacs'], chnl_infs['prods'] = [], []
    for side in ('reacs', 'prods'):
        for rgt in rxn[side]:
            chnl_infs_i, model_basis_energy_dct = build.read_spc_data(
                spc_dct, rgt,
                chn_pf_models, chn_pf_levels,
                run_prefix, save_prefix, model_basis_energy_dct,
                ref_pf_models=ref_pf_models,
                ref_pf_levels=ref_pf_levels)
            chnl_infs[side].append(chnl_infs_i)
        if side in rxn['dummy']:
            symm_barrier = True
            # for _ in range(len(rxn[side])):
            #     chnl_infs[side].append({'ene_chnlvl': 0.00})

    # Set up data for TS
    chnl_infs['ts'] = []
    chnl_infs['ts'], model_basis_energy_dct = build.read_ts_data(
        spc_dct, tsname, rxn['reacs'], rxn['prods'],
        chn_pf_models, chn_pf_levels,
        run_prefix, save_prefix, model_basis_energy_dct,
        ts_class, ts_sadpt, ts_nobarrier,
        ref_pf_models=ref_pf_models, ref_pf_levels=ref_pf_levels)

    # if chnl_infs['ts']['writer'] in ('pst_block', 'vrctst_block'):
    #     if len(chnl_infs['reacs']) == 2:
    #         ts_ene = sum(inf['ene_chnlvl'] for inf in chnl_infs['reacs'])
    #     else: 
    #         ts_ene = sum(inf['ene_chnlvl'] for inf in chnl_infs['prods'])
    #     chnl_infs['ts'].update({'ene_chnlvl': ts_ene})

    chnl_infs['ts']['symm_barrier'] = symm_barrier

    # Set up the info for the wells
    rwell_model = chn_pf_models['rwells']
    if need_fake_wells(ts_class, rwell_model):
        chnl_infs['fake_vdwr'] = copy.deepcopy(chnl_infs['reacs'])
    pwell_model = chn_pf_models['pwells']
    if need_fake_wells(ts_class, pwell_model):
        chnl_infs['fake_vdwp'] = copy.deepcopy(chnl_infs['prods'])

    return chnl_infs, model_basis_energy_dct
