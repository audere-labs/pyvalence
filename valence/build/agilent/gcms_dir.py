from valence import utils
from .gcms_data import GcmsData
from .gcms_results import GcmsResults

FILE_STR = {
    'acqmeth.txt': None,
    'audit.txt': None,
    'cnorm.ini': None,
    'data.ms': GcmsData,
    'fames-ha.res': None,
    'fames-ha.xls': None,
    'fileinfo.txt': None,
    'ls_report': None,
    'percent.txt': None,
    'pre_post.ini': None,
    'qreport.txt': None,
    'results.csv': GcmsResults
}


class GcmsDir(object):
    ''' read Agilent gcms files from provided directory

        Arguments:
            dir_path: directory to agilent gcms files

        Attributes:
            data: data extracted from data.ms as pd DataFrame
            results: data extracted from results.csv as pd DataFrame
    '''
    def __init__(self, dir_path, file_str=FILE_STR):
        self.dir_path = dir_path
        self.file_str = file_str
        self.files = {fn.lower(): fp for fn, fp in utils.diriter(dir_path)}
        self._data = {fn.lower(): None for fn in self.files}

    def _data_cache(self, key):
        ''' load or return data associated with file key
        '''
        # TODO: organize / refactor exceptions
        if key not in self._data:
            raise KeyError(
                '{} not in {}'.format(key, self.dir_path))
        if key not in self.file_str:
            raise KeyError(
                '{} not a recognized file'.format(key))
        if not self.file_str[key]:
            raise NotImplementedError(
                'parser for {} not yet implemented'.format(key))

        if self._data[key] is None:
            self._data[key] = self.file_str[key](self.files[key])
        return self._data[key]

    @property
    def data(self):
        ''' return data from data.ms
        '''
        return self._data_cache('data.ms')

    @property
    def results(self):
        ''' return data from results.csv
        '''
        return self._data_cache('results.csv')
