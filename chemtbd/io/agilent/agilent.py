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
            [dir_key]: GcmsDir object associated with dir_key
            keys: dir_keys
            data: 
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
    

    def __init__(self, dir_list, dir_keys = None):
        if not dir_keys:
            dir_keys = [os.path.basename(path) for path in dir_list]
        self._folders = {
            k: GcmsDir(v) for k, v in zip(dir_keys, dir_list)
        }

    def __getitem__(self, key):
        return self._folders[key]
    
    def stack_results(self, attr):
        ''' this is sloppy - TODO: refactor
        '''
        dfs = []
        for key, val in self._folders.items():
            df = val.results[attr]
            if not df is None:
                dfs.append(df.assign(key = key))
        return pd.concat(dfs, axis=0)

    def stack_data(self, attr):
        ''' this is sloppy - TODO: refactor
        '''
        dfs = []
        for key, val in self._folders.items():
            df = val.data[attr]
            if not df is None:
                dfs.append(df.assign(key = key))
        return pd.concat(dfs, axis=0)

    def keys(self):
        ''' get dir_keys
        '''
        return self._folders.keys()

    def data(self, attr):
        ''' get data attr from all folders as stacked DataFrame
        '''
        return self.stack_data(attr)

    def results(self, attr):
        ''' get result attr from all folders as stacked DataFrame
        '''
        return self.stack_results(attr)
