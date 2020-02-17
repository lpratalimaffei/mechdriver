""" Dictionary of standard bond lengths
"""

from lib.phydat.phycon import ANG2BOHR

# Dictionary of A-B single bond lengths
LEN_DCT = {
    ('H', 'H'): 0.74 * ANG2BOHR,
    ('C', 'H'): 1.09 * ANG2BOHR,
    ('C', 'C'): 1.54 * ANG2BOHR,
    ('C', 'N'): 1.47 * ANG2BOHR,
    ('C', 'O'): 1.43 * ANG2BOHR,
    ('N', 'H'): 1.01 * ANG2BOHR,
    ('N', 'N'): 1.45 * ANG2BOHR,
    ('N', 'O'): 1.45 * ANG2BOHR,
    ('O', 'O'): 1.30 * ANG2BOHR,
    ('O', 'H'): 0.95 * ANG2BOHR,
}
