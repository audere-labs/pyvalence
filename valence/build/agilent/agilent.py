""" Read GCMS Files produced by Agilent

    Todo:
        Establish robust exception handling
        Final sign-off on Agilent Gcms property names
"""
import os
import pandas as pd

from .gcms_dir import GcmsDir


class AgilentGcms(object):
    """ Read Agilent GCMS files into collections of pandas DataFrames.

        Attributes:
            keys: Index of DataFrame corresponding to the names
                  of imported Agilent folders
            datams: data collected from data.ms files as DataFrame
            results_fid: fid table from results.csv files as DataFrame
            results_lib: lib table from results.csv files as DataFrame
            results_tic: tic table from result.csv files as DataFrame

        Returns:
            valence.build.AgilentGcms object containing pandas DataFrames
            constructed from data collected from Agilent GCMS files

        Example:
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
        """ initialize from single Agilent directory
        """
        dir_list = [agilent_dir]
        return cls(dir_list)

    @classmethod
    def from_root(cls, root_dir):
        """ initialize from root directory containing only
            Agilent directories
        """
        dir_list = [os.path.join(root_dir, path)
                    for path in next(os.walk(root_dir))[1]]
        return cls(dir_list)

    def _common_stack(self, accessor, attr):
        """ load all attr from accessor and stack in single df
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

    def keys(self):
        """ keys representing folder names
        """
        return self._folders.keys()

    @property
    def datams(self):
        """ data.ms from all folders as stacked DataFrame
        """
        return self._datams

    @property
    def results_fid(self):
        """ results.csv fid data from all folders as stacked DataFrame
        """
        return self._results_fid

    @property
    def results_lib(self):
        """ results.csv lib data from all folders as stacked DataFrame
        """
        return self._results_lib

    @property
    def results_tic(self):
        """ results.csv tic data from all folders as stacked DataFrame
        """
        return self._results_tic
