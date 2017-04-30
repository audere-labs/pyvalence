import struct
import numpy as np
import pandas as pd
from chemtbd.io.agilent.gcms_base import GcmsIoBase

'''
    io for Agilent DATA.ms file
'''

TIC_COLSTR = {
    'tic': ('tic', 'f4'),   
}
TME_COLSTR = {
    'tme': ('tme', 'f4')
}
COLSTR_KEY = {'tic': TIC_COLSTR, 'tme': TME_COLSTR}

def reader(file_path):

    def total_trace(file_path):
        '''
            source: https://github.com/bovee/Aston/blob/master/aston/tracefile/agilent_ms.py
            TODO: verify, optimize
        '''

        f = open(file_path, 'rb')

        # get number of scans to read in
        f.seek(0x5)
        if f.read(4) == 'GC':
            f.seek(0x142)
        else:
            f.seek(0x118)
        nscans = struct.unpack('>H', f.read(2))[0]

        # find the starting location of the data
        f.seek(0x10A)
        f.seek(2 * struct.unpack('>H', f.read(2))[0] - 2)

        tme = np.zeros(nscans)
        tic = np.zeros(nscans)
        for i in range(nscans):
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]
            tme[i] = struct.unpack('>I', f.read(4))[0] / 60000.
            f.seek(npos - 4)
            tic[i] = struct.unpack('>I', f.read(4))[0]
            f.seek(npos)
        f.close()
        return [], [[['tic']] + tic.tolist(), [['tme']] + tme.tolist()]
    return total_trace(file_path)


class GcmsData(GcmsIoBase):
    ''' manages reading of Agilent DATA.MS
        and mutation of tables into single pandas df
        
        Arguments:
            file_path: path to DATA.MS file

        Attributes:
            data: tic, tme tables as single DataFrame
            tic: tic column from data
            tme: tme column from data

        Methods:
            __call__: returns data attribute
    '''
    def __init__(self, file_path):
        super().__init__(COLSTR_KEY, reader, file_path)

    @property
    def tic(self):
        ''' return tic series '''
        return self._access('tic')
    
    @property
    def tme(self):
        ''' return tme series '''
        return self._access('tme')

