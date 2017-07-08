""" Read GCMS Files produced by Agilent
"""
import os
import pandas as pd

from .gcms_dir import GcmsDir


class AgilentGcms(object):
    """ Read Agilent GCMS files into collections of pandas DataFrames.

        Parameters
        ----------
            dir_list : list(str)
                Agilent ``.D`` directories.
            dir_keys : list(str), optional
                Names for elements in ``dir_list`` parameter.

        Example
        -------
            >>> gcms_data = AgilentGcms(['./data/FA01.D', './data/FA02.D'])
            >>> print(gcms_data.keys())
            ['FA01.D', 'FA02.D']
            >>> gcms_data = AgilentGcms.from_dir('./data/FA01.D')
            >>> print(gcms_data.keys())
            ['FA01.D']
            >>> gcms_data = AgilentGcms.from_root('./data)
            >>> print(gcms_data.keys())
            ['FA01.D', 'FA02.D']
            >>> agi.datams.columns
            Index(['tic', 'tme'], dtype='object')
            >>> agi.datams.index.name
            'key'
    """
    @classmethod
    def from_dir(cls, agilent_dir):
        """ Initialize from single Agilent folder.

            Parameters
            ----------
            agilent_dir : str
                Path to Agilent ``.D`` folder.
        """
        dir_list = [agilent_dir]
        return cls(dir_list)

    @classmethod
    def from_root(cls, root_dir):
        """ Initialize from root folder containing at least one Agilent ``.D``
            folder.

            Parameters
            ----------
            root_dir : str
                Path to folder containing at least one Agilent ``.D`` folder.
        """
        dir_list = [os.path.join(root_dir, path)
                    for path in next(os.walk(root_dir))[1]]
        return cls(dir_list)

    def _common_stack(self, accessor, attr):
        """ Load all attr from accessor and stack in single DataFrame.

            Parameters
            ----------
            accessor : str
            attr : str
        """
        dfs = []
        for key, val in self._folders.items():
            df = getattr(val, accessor)[attr]
            if df is not None:
                dfs.append(df.assign(key=key))
        return pd.concat(dfs, axis=0).set_index('key')

    def __init__(self, dir_list, dir_keys=None):
        if not dir_keys:
            dir_keys = [os.path.basename(path) for path in dir_list]

        self._folders = {
            k: GcmsDir(v) for k, v in zip(dir_keys, dir_list)
        }

        self._results_tic = self._common_stack('results', 'tic')
        self._results_fid = self._common_stack('results', 'fid')
        self._results_lib = self._common_stack('results', 'lib')
        self._datams = self._common_stack('data', 'data')

    @property
    def keys(self):
        """ list(str): keys representing folder names
        """
        return self._folders.keys()

    @property
    def datams(self):
        """ DataFrame: ``DATA.MS` data extracted from ``.D`` folders.
        """
        return self._datams

    @property
    def results_fid(self):
        """ DataFrame: ``RESULTS.CSV`` fid data from ``.D`` folders
        """
        return self._results_fid

    @property
    def results_lib(self):
        """ DataFrame: ``RESULTS.CSV`` lib data from `.D` folders
        """
        return self._results_lib

    @property
    def results_tic(self):
        """ DataFrame: ``RESULTS.CSV`` tic data from all `.D` folders
        """
        return self._results_tic
