import struct
import numpy as np
import scipy.sparse
import pandas as pd
from chemtbd.io.agilent.gcms_base import GcmsIoBase

'''
    io for Agilent DATA.ms file
'''

DATA_COLSTR = {
    'tic': ('tic', 'f4'),   
    'tme': ('tme', 'f4')
}
COLSTR_KEY = {'data': DATA_COLSTR}

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
        jj = [['tic', 'tme']] + [list(a) for a in list(zip(tic, tme))]
        return [], [jj]
    return total_trace(file_path)


def read_wut(file_path):
    '''
        source: https://github.com/bovee/Aston/blob/master/aston/tracefile/agilent_ms.py
        TODO: verify, optimize
    '''
    
    f = open(file_path, 'rb')

    # get number of scans to read in
    # note that GC and LC chemstation store this in slightly different
    # places
    f.seek(0x5)
    if f.read(4) == 'GC':
        f.seek(0x142)
    else:
        f.seek(0x118)
    nscans = struct.unpack('>H', f.read(2))[0]

    f.seek(0x10A)
    f.seek(2 * struct.unpack('>H', f.read(2))[0] - 2)
    dstart = f.tell()

    # determine total number of measurements in file
    tot_pts = 0
    rowst = np.empty(nscans + 1, dtype=int)
    rowst[0] = 0

    for scn in range(nscans):
        # get the position of the next scan
        npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]

        # keep a running total of how many measurements
        tot_pts += (npos - f.tell() - 26) / 4
        rowst[scn + 1] = tot_pts

        # move forward
        f.seek(npos)

    # go back to the beginning and load all the other data
    f.seek(dstart)

    ions = []
    i_lkup = {}
    cols = np.empty(int(tot_pts), dtype=np.int)
    vals = np.empty(int(tot_pts), dtype=np.int)
    times = np.empty(nscans)

    for scn in range(nscans):
        npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]

        # the sampling rate is evidentally 60 kHz on all Agilent's MS's
        times[scn] = struct.unpack('>I', f.read(4))[0] / 60000.

        f.seek(f.tell() + 12)
        npts = rowst[scn + 1] - rowst[scn]
        mzs = struct.unpack('>' + npts * 'HH', f.read(npts * 4))

        nions = set(mzs[0::2]).difference(i_lkup)
        i_lkup.update({ion: i + len(ions) for i, ion in enumerate(nions)})
        ions += nions

        cols[rowst[scn]:rowst[scn + 1]] = [i_lkup[i] for i in mzs[0::2]]
        vals[rowst[scn]:rowst[scn + 1]] = mzs[1::2]
        f.seek(npos)
    f.close()

    vals = ((vals & 16383) * 8 ** (vals >> 14)).astype(float)
    data = scipy.sparse.csr_matrix((vals, cols, rowst),
                                    shape=(nscans, len(ions)), dtype=float)
    ions = np.array(ions) / 20.

    return data, times, ions


class GcmsData(GcmsIoBase):
    ''' manages reading of Agilent DATA.MS
        and mutation of tables into single pandas df
        
        Arguments:
            file_path: path to DATA.MS file

        Attributes:
            data: tic, tme arrays as single DataFrame
    '''
    def __init__(self, file_path):
        self.file_path = file_path
        super().__init__(COLSTR_KEY, reader, file_path)

    @property
    def data(self):
        ''' return tic, tme data '''
        return self['data']
    
    @property
    def chromatogram(self):
        ''' test read '''
        data, time, ions =  read_wut(self.file_path)
        return pd.DataFrame(data=data.todense(), index=time, columns=ions)
