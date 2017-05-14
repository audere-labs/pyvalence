import os
import pandas as pd
from chemtbd import utils
from .gcms_dir import GcmsDir


class Agilent(object):
    ''' read Agilent gcms files from provided directories

        Constructors:
            default:  list of agilent dir paths
            from_dir: single agilent dir path
            from_root: dir path containing only agilent dirs
            from_list: same as default

        Attributes:
            keys: dir_keys
            datams: data collected from data.ms files as DataFrame
            results_fid: fid table from results.csv files as DataFrame
            resutls_lib: lib table from results.csv files as DataFrame
            results_tic: tic table from result.csv files as DataFrame
    '''

    @classmethod
    def from_dir(cls, agilent_dir):
        ''' initialize from single agilent dir
        '''
        dir_list = [agilent_dir]
        return cls(dir_list)

    @classmethod
    def from_root(cls, root_dir):
        ''' initialize from directory containing only
            agilent dirs
        '''
        dir_list = [os.path.join(root_dir, path)
                    for path in next(os.walk(root_dir))[1]]
        return cls(dir_list)

    @classmethod
    def from_list(cls, dir_list, dir_keys = None):
        ''' initialize from list of directory paths
        '''
        return cls(dir_list, dir_keys)
    
    def common_stack(self, accessor, attr):
        ''' load all attr from accessor and stack in single df
        '''
        dfs = []
        for key, val in self._folders.items():
            df = getattr(val, accessor)[attr]
            if not df is None:
                dfs.append(df.assign(key=key))
        return pd.concat(dfs, axis=0).set_index('key')

    def __init__(self, dir_list, dir_keys = None):
        if not dir_keys:
            dir_keys = [os.path.basename(path) for path in dir_list]
        
        self._folders = {
            k: GcmsDir(v) for k, v in zip(dir_keys, dir_list)
        }

        self._results_tic = self.common_stack('results', 'tic')
        self._results_fid = self.common_stack('results', 'fid')
        self._results_lib = self.common_stack('results', 'lib')
        self._datams = self.common_stack('data', 'data')

    def keys(self):
        ''' get dir_keys
        '''
        return self._folders.keys()
    
    @property
    def datams(self):
        ''' data.ms from all folders as stacked DataFrame
        '''
        return self._datams
    
    @property
    def results_fid(self):
        ''' results.csv fid data from all folders as stacked DataFrame
        '''
        return self._results_fid
    
    @property
    def results_lib(self):
        ''' results.csv lib data from all folders as stacked DataFrame
        '''
        return self._results_lib

    @property
    def results_tic(self):
        ''' results.csv tic data from all folders as stacked DataFrame
        '''
        return self._results_tic

