"""
  Libraries to check for allowed and supported keywords
"""

# Run Keywords
RUN_INP_REQUIRED_KEYWORDS = [
    'mech',
    'spc'
]
RUN_INP_SUPPORTED_KEYWORDS = [
    'mech',
    'spc',
    'run_prefix',
    'save_prefix',
    'print_mech'
]
RUN_INP_KEY_DCT = {
    'mech': ['chemkin'],
    'spc': ['csv'],
    'print_mech': [True, False]
}
RUN_SUPPORTED_KEYWORDS = [
    'es',
    'thermochem',
    'kinetics',
    'write_messpf',
    'run_messpf',
    'run_nasa',
    'write_messrate',
    'run_messrate',
    'run_fits',
    'transport'
]

# Model keywords
MODEL_PF_SUPPORTED_DCT = {
    'ene': ['sp', 'composite'],
    'rot': ['rigid', 'vpt2'],
    'vib': ['harm', 'vpt2', 'tau'],
    'tors': ['rigid', '1dhr', '1dhrf', '1dhrfa', 'mdhr', 'mdhrv', 'tau'],
    'sym': ['none', 'sampling', '1dhr'],
    'ts_barrierless': ['pst', 'rpvtst', 'vrctst'],
    'ts_sadpt': ['fixed', 'pst', 'rpvtst', 'vrctst'],
    'wells': ['fake', 'find', 'none'],
    'rwells': ['fake', 'find', 'none'],
    'pwells': ['fake', 'find', 'none'],
    'tunnel': ['none', 'eckart', 'sct'],
    'etrans': ['none', 'estimate', 'read']
}
MODEL_PF_DEFAULT_DCT = {
    'ene': 'sp',
    'rot': 'rigid',
    'vib': 'harm',
    'tors': 'rigid',
    'sym': 'none',
    'ts_nobar': 'pst',
    'ts_sadpt': 'fixed',
    'wells': 'fake',
    'tunnel': 'none',
    'etrans': 'estimate'
}

# Electronic Structure Tasks
ES_TSK_OBJ_SUPPORTED_LST = [
    'spc',
    'ts',
    'vdw'
]
ES_TSK_SUPPORTED_DCT = {
    'spc': [
        'init_geom',
        'conf_samp', 'conf_energy', 'conf_grad', 'conf_hess',
        'conf_vpt2', 'conf_prop', 'conf_opt',
        'hr_scan', 'hr_energy', 'hr_grad', 'hr_hess', 'hr_vpt2', 'hr_reopt',
        'tau_samp', 'tau_energy', 'tau_grad', 'tau_hess'],
    'ts': [
        'find_ts',
        'find_sadpt', 'find_molrad_vtst', 'find_radrad_vtst', 'find_vrctst',
        'conf_samp', 'conf_energy', 'conf_grad', 'conf_hess',
        'conf_vpt2', 'conf_prop',
        'hr_scan', 'hr_energy', 'hr_grad', 'hr_hess', 'hr_vpt2', 'hr_reopt',
        # 'tau_samp', 'tau_energy', 'tau_grad', 'tau_hess',
        'irc_scan', 'irc_energy', 'irc_grad', 'irc_hess',
        'drp_samp', 'drp_energy', 'drp_grad', 'drp_hess'],
    'vdw': [
        'find',
        'conf_samp', 'conf_energy', 'conf_grad', 'conf_hess']
}
ES_TSK_KEYWORDS_SUPPORTED_DCT = {
    'init_geom': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'find_ts': ['runlvl', 'inplvl', 'rxndirn',
                'var_splvl1', 'var_splvl2', 'var_scnlvl',
                'nobarrier', 'retryfail', 'overwrite'],
    'find_sadpt': ['runlvl', 'inplvl', 'rxndirn',
                   'nobarrier', 'retryfail', 'overwrite'],
    'find_molrad_vtst': ['runlvl', 'inplvl', 'rxndirn',
                         'var_splvl1', 'var_splvl2', 'var_scnlvl',
                         'nobarrier', 'retryfail', 'overwrite'],
    'find_radrad_vtst': ['runlvl', 'inplvl', 'rxndirn',
                         'var_splvl1', 'var_splvl2', 'var_scnlvl',
                         'nobarrier', 'pot_thresh',
                         'retryfail', 'overwrite'],
    'find_vrctst': ['runlvl', 'inplvl', 'rxndirn',
                    'var_splvl1', 'var_splvl2', 'var_scnlvl',
                    'nobarrier', 'retryfail', 'overwrite'],
    'conf_samp': ['runlvl', 'inplvl', 'cnf_range', 'retryfail', 'overwrite'],
    'conf_energy': ['runlvl', 'inplvl', 'cnf_range', 'retryfail', 'overwrite'],
    'conf_grad': ['runlvl', 'inplvl', 'cnf_range', 'retryfail', 'overwrite'],
    'conf_hess': ['runlvl', 'inplvl', 'cnf_range', 'retryfail', 'overwrite'],
    'conf_vpt2': ['runlvl', 'inplvl', 'cnf_range', 'retryfail', 'overwrite'],
    'conf_prop': ['runlvl', 'inplvl', 'cnf_range', 'retryfail', 'overwrite'],
    'conf_opt': ['runlvl', 'inplvl', 'cnf_range', 'retryfail', 'overwrite'],
    'hr_scan': ['runlvl', 'inplvl', 'tors_model', 'resamp_min',
                'retryfail', 'overwrite'],
    'hr_grad': ['runlvl', 'inplvl', 'tors_model',
                'retryfail', 'overwrite'],
    'hr_hess': ['runlvl', 'inplvl', 'tors_model',
                'retryfail', 'overwrite'],
    'hr_energy': ['runlvl', 'inplvl', 'tors_model',
                  'retryfail', 'overwrite'],
    'hr_vpt2': ['runlvl', 'inplvl', 'tors_model',
                'retryfail', 'overwrite'],
    'hr_reopt': ['runlvl', 'inplvl', 'tors_model',
                 'retryfail', 'overwrite', 'hrthresh'],
    'tau_samp': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'tau_energy': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'tau_grad': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'tau_hess': ['runlvl', 'inplvl', 'hessmax', 'retryfail', 'overwrite'],
    'irc_scan': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'irc_energy': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'irc_grad': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'irc_hess': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'drp_scan': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'drp_energy': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'drp_grad': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
    'drp_hess': ['runlvl', 'inplvl', 'retryfail', 'overwrite'],
}
ES_TSK_KEYWORDS_VAL_SUPPORTED_DCT = {
    'tors_model': ['1dhr', '1dhrf', '1dhrfa', 'mdhr'],
    'cnf_range': ['min'],
    'nobarrier': ['pst', 'rpvtst', 'vrctst'],
    'retryfail': [True, False],
    'overwrite': [True, False],
    'rxndirn': ['forw', 'back', 'exo'],
    'resamp_min': [True, False]
}
ES_TSK_KEYWORDS_DEFAULT_DCT = {
    'runlvl': None,
    'inplvl': None,
    'var_splvl1': None,
    'var_splvl2': None,
    'var_scnlvl': None,
    'tors_model': '1dhr',
    'cnf_range': 'min',
    'nobarrier': 'pst',
    'retryfail': True,
    'overwrite': False,
    'rxndirn': 'forw',
    'hessmax': 1000,
    'hrthresh': -0.5,
    'pot_thresh': 0.3
}

# Species keywords
SPC_REQUIRED_KEYWORDS = [
    'mult',
    'charge',
]
SPC_SUPPORTED_KEYWORDS = [
    'charge',
    'mult',
    'geom',
    'mc_nsamp',
    'tau_nsamp',
    'hind_inc',
    'tors_names',
    'elec_levels',
    'sym_factor',
    'inchi',
    'smiles',
    'geom',
    'kickoff',
    'ts_search',
    'active',
    'zma_idx',
    # etrans
    'smin',
    'smax',
    'etrans_nsamp',
    'kt_pst',
    'temp_pst',
    'n_pst',
    'lj',
    'edown'
]
SPC_DEFAULT_DCT = {
    'kickoff': [0.1, False],
    'pst_params': [1.0, 6],
    'hind_inc': 30.0,
    'mc_nsamp': [True, 12, 1, 3, 100, 25],
    'tau_nsamp': [True, 12, 1, 3, 100, 25],
    'sym_factor': 1.0,
    'lj': None,
    'edown': None
}

# Theory Keywords
THY_REQUIRED_KEYWORDS = [
    'program',
    'method',
    'basis',
    'orb_res'
]
THY_SUPPORTED_KEYWORDS = [
    'program',
    'method',
    'basis',
    'orb_res',
    'ncycles',
    'mem',
    'nprocs',
    'econv',
    'gconv'
]

# ETrans
TRANS_TSK_SUPPORTED_DCT = {
    'spc': ['onedmin']
}
TRANS_TSK_KEYWORDS_SUPPORTED_DCT = {
    'onedmin': ['runlvl', 'inplvl', 'bath', 'pot',
                'njobs', 'nsamp',
                'smin', 'smax', 'conf',
                'retryfail', 'overwrite']
}
TRANS_TSK_KEYWORDS_VAL_SUPPORTED_DCT = {
    'retryfail': [True, False],
    'overwrite': [True, False],
}
TRANS_TSK_KEYWORDS_VAL_DEFAULT_DCT = {
    'pot': 'lj_12_6',
    'njobs': 1,
    'nsamp': 1,
    'smin': 2.0,
    'smax': 6.0,
    'conf': 'sphere',
    'retryfail': True,
    'overwrite': False,
}
