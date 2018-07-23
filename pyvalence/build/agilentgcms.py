""" Read GCMS files produced by Agilent
"""
import re
import csv
import os
import struct
import numpy as np
import pandas as pd
import scipy.sparse

class AgilentGcmsTableBase(object):
    """ Base class for Agilent GCMS builders. This class should not be
        instantiated directly.
    """
    @classmethod
    def _clean_name(cls, item):
        """ return clean name from colstr item.
        """
        return item[0]

    @classmethod
    def _np_type(cls, item):
        """ return numpy type from colstr item.
        """
        return item[1]

    @classmethod
    def _pd_columns(cls, header, colstr):
        """ return column headers from colstr item.
        """
        return [cls._clean_name(colstr[col]) for col in header]

    @classmethod
    def _column_structure(cls, header, keys):
        """ match table colstr with header read from file
        """
        for key, val in keys.items():
            if set(header) == set(val.keys()):
                return key, val
        raise Exception(
            'expected column structure: {}, found {}'.format(
                val.keys(), header)
        )

    def __init__(self, col_keys, reader, file_path):
        if self.__class__.__name__ == 'AgilentGcmsTableBase':
            raise ValueError('This class is not intended'
                             'to be instantiated directly.')
        self.col_keys = col_keys
        self._meta, self._tables = reader(file_path)
        self._data = {}

    def _as_dataframe(self, header, data):
        """ transform results of reader function to pandas.DataFrame
            with appropriate column names and data types
        """
        key, colstr = self._column_structure(header, self.col_keys)
        df = (pd.DataFrame(data, columns=self._pd_columns(header, colstr))
                .apply(pd.to_numeric, errors='ignore'))
        return (key, df)

    def _build_data(self):
        """ convert list of tables to dictionary of pandas dataframe
        """
        def build(tbl):
            return self._as_dataframe(tbl[0], tbl[1:])
        return {key: df for key, df in map(build, self._tables)}

    def _access(self, key):
        """ provide access to key in data with appropriate
            exception handling
        """
        if not self._data:
            self._data = self._build_data()
        if key not in self._data:
            self._data[key] = None
        return self._data[key]

    def __getitem__(self, key):
        """ provide access to key in data
        """
        return self._access(key)

class AgilentGcmsResults(AgilentGcmsTableBase):
    """ Manages reading of Agilent RESULT.CSV
        and mutation of tables into single pandas df

        Arguments:
            file_path: path to RESULTS.CSV file
    """
    __tic_colstr = {
        'Header=': ('header=', 'O'),
        'Peak': ('peak', 'i4'),
        'R.T.': ('rt', 'f4'),
        'First': ('first', 'i4'),
        'Max': ('max', 'i4'),
        'Last': ('last', 'i4'),
        'PK  TY': ('pk_ty', 'O'),
        'Height': ('height', 'i4'),
        'Area': ('area', 'i4'),
        'Pct Max': ('pct_max', 'f4'),
        'Pct Total': ('pct_total', 'f4')
    }

    __lib_colstr = {
        'Header=': ('header=', 'O'),
        'PK': ('pk', 'i4'),
        'RT': ('rt', 'f4'),
        'Area Pct': ('pct_area', 'f4'),
        'Library/ID': ('library_id', 'O'),
        'Ref': ('ref', 'i4'),
        'CAS': ('cas', 'O'),
        'Qual': ('qual', 'i4'),
    }

    __fid_colstr = {
        'Header=': ('header=', 'O'),
        'Peak': ('peak', 'i4'),
        'R.T.': ('rt', 'f4'),
        'Start': ('first', 'i4'),
        'End': ('end', 'i4'),
        'PK TY': ('pk_ty', '0'),
        'Height': ('height', 'i4'),
        'Area': ('area', 'i4'),
        'Pct Max': ('pct_max', 'f4'),
        'Pct Total': ('pct_total', 'f4')
    }

    __colstr_key = {
        'tic': __tic_colstr,
        'lib': __lib_colstr,
        'fid': __fid_colstr
    }

    @staticmethod
    def _results_reader(file_path):
        """ read Agilent RESULTS.CSV into list of lists where each list item
            is the lines representing a tic, fid, or lib table
        """
        def istablerow(line):
            """ return true if line is table row
            """
            return re.match('\d+=', line)

        def isheader(line):
            """ return true if line is header
            """
            return line[0] == 'Header='

        def seek_rows(header, gen):
            """ gen is at position after header seek until
                no more table rows or stopiter exception
            """
            table = [header]
            try:
                while True:
                    line = next(gen)
                    if not istablerow(line[0]):
                        break
                    table.append(line)
            except StopIteration as e:
                line = None
            finally:
                return line, table

        def scan_csv(gen):
            """ split csv generator into meta information
                and list of individual tables of tokens
            """
            meta, tables = [], []
            try:
                while True:
                    line = next(gen)
                    if isheader(line):
                        line, table = seek_rows(line, gen)
                        tables.append(table)
                    if line:
                        meta.append(line)
            except StopIteration as e:
                return meta, tables

        return scan_csv(csv.reader(open(file_path)))

    def __init__(self, file_path):
        super().__init__(self.__colstr_key, self._results_reader, file_path)

    @property
    def tic(self):
        ''' return tic table
        '''
        return self['tic']

    @property
    def lib(self):
        ''' return lib table
        '''
        return self['lib']

    @property
    def fid(self):
        ''' return fid table
        '''
        return self['fid']

class AgilentGcmsDataMs(AgilentGcmsTableBase):
    """ Manages reading of Agilent DATA.MS file
        and stacking into single pandas DataFrame

        Parameters
        ----------
        file_path : str
            Path to DATA.MS file.
    """

    __chrom_colstr = {
        'tic': ('tic', 'f4'),
        'tme': ('tme', 'f4')
    }

    __colstr_key = {
        'chromatogram': __chrom_colstr
    }

    @classmethod
    def access_colstr(attr):
        ''' return header only
        '''
        if attr in __colstr_key:
            return __colstr_key[attr]
        return None

    @staticmethod
    def _read_chromatogram(file_path):
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
    
    @staticmethod
    def _read_spectra(file_path):
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

    def __init__(self, file_path):
        self._spectra = self._read_spectra(file_path)
        super().__init__(self.__colstr_key, self._read_chromatogram, file_path)

    @property
    def spectra(self):
        """ WIP: For testing chromatogram build
        """
        return self._spectra

    @property
    def chromatogram(self):
        """
        """
        return self['chromatogram']

class AgilentGcfid(AgilentGcmsTableBase):
    """ Manages reading of Agilent DATA.MS file
        and stacking into single pandas DataFrame

        Parameters
        ----------
        file_path : str
            Path to DATA.MS file.
    """

    __chrom_colstr = {
        'fid': ('fid', 'f4'),
        'tme': ('tme', 'f4')
    }

    __colstr_key = {
        'chromatogram_fid': __chrom_colstr
    }

    @classmethod
    def access_colstr(attr):
        ''' return header only
        '''
        if attr in __colstr_key:
            return __colstr_key[attr]
        return None

    @staticmethod
    def _read_chromatogram_fid(file_path):
        """ Extract fid and tme data from FID1A.ch file

            Args:
                file_path (str): path to FID1A.ch file

            Returns:
                ([meta], [data]): ``meta`` is the metadata lines
                in the FID1A.ch file.  ``data`` is the fid and tme lines
                from the FID1A.ch file as [fid, tme].
        """
        f = open(file_path, 'rb')

        f.seek(0x11A)
        start_time = struct.unpack('>f', f.read(4))[0] / 60000.
        end_time = struct.unpack('>f', f.read(4))[0] / 60000.

        f.seek(0x1800)
        fid = np.fromfile(f, '<f8')
        tme = np.linspace(start_time, end_time, fid.shape[0]) 

        jj = [['fid', 'tme']] + [list(a) for a in list(zip(fid, tme))]
        return [], [jj]  
    

    def __init__(self, file_path):
        super().__init__(self.__colstr_key, self._read_chromatogram_fid, file_path)

    @property
    def spectra(self):
        """ WIP: For testing chromatogram build
        """
        return self._spectra

    @property
    def chromatogram(self):
        """
        """
        return self['chromatogram_fid']

class AgilentGcmsDir(object):
    """ Read all GCMS files from Agilent .D folder.

        Parameters
        ----------
        dir_path : str
            Path to Agilent .D folder.
    """

    __file_str = {
        'acqmeth.txt': None,
        'audit.txt': None,
        'cnorm.ini': None,
        'data.ms': AgilentGcmsDataMs,
        'fames-ha.res': None,
        'fames-ha.xls': None,
        'fileinfo.txt': None,
        'ls_report': None,
        'percent.txt': None,
        'pre_post.ini': None,
        'qreport.txt': None,
        'results.csv': AgilentGcmsResults,
        'fid1a.ch':AgilentGcfid
    }

    @classmethod
    def _diriter(cls, dir_path):
        """ Non-public method that returns all files in Agilent .D folder.

            Parameters
            ----------
            dir_path : str
                Path to Agilent .D folder.

            Returns
            -------
            Generator
                Itarable over files in ``dir_path``.
        """
        return ((f, os.path.join(root, f))
                for root, dirs, files in os.walk(dir_path)
                for f in files if f.lower() in cls.__file_str)

    def __init__(self, dir_path):
        self._dir_path = dir_path
        self._files = {fn.lower(): fp
                       for fn, fp in AgilentGcmsDir._diriter(dir_path)}
        self._data = {fn.lower(): None for fn in self._files}

    def _key_validate(self, key):
        """ Non-public method to validate build of file in Agilent .D folder.

            Parameters
            ----------
            key : str
                Name of file in Agilent .D folder.

            Raises
            ------
            KeyError 
                Raised iff ``key`` not a known Agilent .D file, or if ``key``
                is a known Agilent .D file, but was not present in the
                provided ``_dir_path``.
            NotImplementedError
                If build object associated with ``key`` is not implemented.
        """
        if key not in self._data:
            raise KeyError(
                '{} not in {}'.format(key, self._dir_path)
            )
        if key not in AgilentGcmsDir.__file_str:
            raise KeyError(
                '{} not a recognized file'.format(key)
            )
        if not AgilentGcmsDir.__file_str[key]:
            raise NotImplementedError(
                'parser for {} not yet implemented'.format(key)
            )

    def _data_cache(self, key):
        """ Non-public accessor for loading or getting data associated
            with ``key``. Performs appropriate validation on ``key``.

            Parameters
            ----------
            key : str
                File key associated with data to load or get.

            Returns
            -------
            DataFrame
                Data loaded from file associated with ``key``.
        """
        self._key_validate(key)        
        if self._data[key] is None:
            self._data[key] = AgilentGcmsDir.__file_str[key](self._files[key])
        return self._data[key]

    @property
    def datams(self):
        """ obj: AgilentGcmsDataMs built from DATA.MS file in
            Agilent .D folder
        """
        return self._data_cache('data.ms')

    
    @property
    def datafid(self):
        return self._data_cache('fid1a.ch')
    @property
    def results(self):
        """ obj: AgilentGcmsResult built from RESULTS.CSV file in
            Agilent .D folder.
        """
        return self._data_cache('results.csv')

class AgilentGcms(object):
    """ Read GCMS files from one or more Agilent .D folders into a collection
        of pandas.DataFrame.

        Parameters
        ----------
        dir_list : list(str)
            Paths to Agilent .D folders.
        dir_keys : list(str)
            Optional. Provide custom names for the .D folders. If omitted,
            the folders' names are used.
    """
    @classmethod
    def from_dir(cls, agilent_dir):
        """ Initialize AgilentGcms from single Agilent .D folder.

            Parameters
            ----------
            agilent_dir : str
                Path to Agilent .D folder.

            Returns
            -------
            obj
                AgilentGcms object constructed from single
                Agilent .D folder
        """
        dir_list = [agilent_dir]
        return cls(dir_list)

    @classmethod
    def from_root(cls, root_dir):
        """ Initialize AgilentGcms from root folder containing at least one
            Agilent .D folder.

            Parameters
            ----------
            root_dir : str
                Path to folder containing at least one Agilent .D folder.

            Returns
            -------
            obj
                AgilentGcms object constructed from a folder containing one
                or more Agilent .D folders
        """
        dir_list = [os.path.join(root_dir, path)
                    for path in next(os.walk(root_dir))[1]]
        return cls(dir_list)

    def _pandas_stack(self, accessor, attr):
        """ Non-public method for stacking all data
        """
        dfs = []
        for key, val in self._folders.items():
            try:
                df = getattr(val, accessor)[attr]
                if df is not None:
                    dfs.append(df.assign(key=key))
            except KeyError:
                # dfs.append(pd.DataFrame({'key': [key]}))
                print(f'missing `{attr}` from `{accessor}` in {key}')

        if not dfs:
            return None
        
        return pd.concat(dfs, axis=0).set_index('key')

    def _dict_stack(self, accessor, attr):
        """ temporary hack to accomodate unstackable spectra
        """
        stack = {}
        for key, val in self._folders.items():
            try:
                stack[key] = getattr(getattr(val, accessor), attr)
            except KeyError:
                print(f'cannot access `{attr}` from `{accessor}` file')
        return stack

    def __init__(self, dir_list, dir_keys=None):
        if not dir_keys:
            dir_keys = [os.path.basename(path) for path in dir_list]
        self._folders = {k: AgilentGcmsDir(v)
                         for k, v in zip(dir_keys, dir_list)}
        self._results_tic = self._pandas_stack('results', 'tic')
        self._results_fid = self._pandas_stack('results', 'fid')
        self._results_lib = self._pandas_stack('results', 'lib')
        self._chromatogram = self._pandas_stack('datams', 'chromatogram')
        self._chromatogram_fid = self._pandas_stack('datafid','chromatogram_fid')
        self._spectra = self._dict_stack('datams', 'spectra')


    @property
    def keys(self):
        """ list(str): Keys representing .D folder names.
        """
        return self._folders.keys()

    @property
    def chromatogram(self):
        """ pandas.DataFrame: DATA.MS data extracted from .D folders.
        """
        return self._chromatogram

    @property
    def chromatogram_fid(self):
        """ pandas.DataFrame: FID.ch data extracted from .D folders.
        """
        return self._chromatogram_fid
    
    @property
    def spectra(self):
        """
        """
        return self._spectra

    @property
    def results_fid(self):
        """ pandas.DataFrame: RESULTS.CSV fid data from .D folders
        """
        return self._results_fid

    @property
    def results_lib(self):
        """ pandas.DataFrame: RESULTS.CSV lib data from .D folders
        """
        return self._results_lib

    @property
    def results_tic(self):
        """ pandas.DataFrame: RESULTS.CSV tic data from all .D folders
        """
        return self._results_tic
