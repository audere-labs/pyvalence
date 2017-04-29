import struct
import numpy as np
import pandas as pd
from chemtbd.agilent.gcms_base import GcmsIoBase

'''
    io for Agilent DATA.ms file
'''

TIC_COLSTR = {
    'tic': ('ms', 'f4'),   
}
TME_COLSTR = {
    'tme': ('ms', 'f4')
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
        return [[['tic']] + tic.tolist(), [['tme']] + tme.tolist()]
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
        super().__init__(COLSTR_KEY)
        self.tables = reader(file_path)

    def _build_data(self):
        ''' convert tables to pandas dataframe
        '''
        build = lambda tbl: self.as_dataframe(tbl[0], tbl[1:])
        return pd.concat(map(build, self.tables), axis=1)

    @property
    def data(self):
        ''' tid, lib and fid as one table with
            rows aligned according to original `Header=` field
        ''' 
        if self._data is None:
            self._data = self._build_data()
        return self._data

    @property
    def tic(self):
        return self.data.filter(regex=r'^tic_', axis=1)
    
    @property
    def tme(self):
        return self.data.filter(regex=r'^tme_', axis=1)

    def __call__(self):
        ''' shortcut to data '''
        return self.data
