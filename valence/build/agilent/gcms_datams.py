""" Extract data from Agilent DATA.MS file

    reader and reader_chromatogram sourced from
    https://github.com/bovee/Aston/blob/master/aston/tracefile/agilent_ms.py

    Todo:
        Finalize name of object, module
        Properly incorporate read_chromatogram
        Investigate / document reader performance and validity
"""
import struct
import numpy as np
import scipy.sparse
import pandas as pd

from .gcms_base import GcmsBuildBase


DATA_COLSTR = {
    'tic': ('tic', 'f4'),
    'tme': ('tme', 'f4')
}
COLSTR_KEY = {'data': DATA_COLSTR}


def reader(file_path):
    """ Extract tic and tme data from DATA.MS file

        Args:
            file_path (str): path to DATA.MS file

        Returns:
            ([meta], [data]): ``meta`` is the metadata lines
            in the DATA.MS file.  ``data`` is the tic and tme lines
            from the DATA.MS file as [tic, tme].
    """
    f = open(file_path, 'rb')

    f.seek(0x5)             # get number of scans to read in
    if f.read(4) == 'GC':
        f.seek(0x142)
    else:
        f.seek(0x118)
    nscans = struct.unpack('>H', f.read(2))[0]

    f.seek(0x10A)            # find the starting location of the data
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


def read_chromatogram(file_path):
    """ Extract chromatogram data from DATA.MS file

        Args:
            file_path (str): path to DATA.MS file

        Returns:
            pandas DataFrame with chromatograph ions as columns,
            time as index, measurements as values
    """
    f = open(file_path, 'rb')

    f.seek(0x5)             # get number of scans to read in
    if f.read(4) == 'GC':   # GC and LC chemstation store in different places
        f.seek(0x142)
    else:
        f.seek(0x118)
    nscans = struct.unpack('>H', f.read(2))[0]

    f.seek(0x10A)
    f.seek(2 * struct.unpack('>H', f.read(2))[0] - 2)
    dstart = f.tell()

    tot_pts = 0             # determine total number of measurements in file
    rowst = np.empty(nscans + 1, dtype=int)
    rowst[0] = 0

    for scn in range(nscans):
        # get the position of the next scan
        npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]

        # keep a running total of how many measurements
        tot_pts += (npos - f.tell() - 26) / 4
        rowst[scn + 1] = tot_pts
        f.seek(npos)        # move forward

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
    data = scipy.sparse.csr_matrix(
        (vals, cols, rowst),
        shape=(nscans, len(ions)),
        dtype=float
    )
    ions = np.array(ions) / 20.
    return pd.DataFrame(data=data.todense(), index=times, columns=ions)


class GcmsDataMs(GcmsBuildBase):
    """ Manages reading of Agilent DATA.MS file
        and stacking into single pandas DataFrame

        Arguments:
            file_path (str): path to DATA.MS file

        Attributes:
            datams (DataFrame): tic and tme arrays as columns
            chromotogram (DataFrame): chromatograph ions as columns,
            time as index, measurements as values
    """
    def __init__(self, file_path):
        self.file_path = file_path
        super().__init__(COLSTR_KEY, reader, file_path)

    @property
    def data(self):
        """ tic and tme data as DataFrame
        """
        return self['data']

    @property
    def chromatogram(self):
        """ WIP: For testing chromatogram build
        """
        return read_chromatogram(self.file_path)
