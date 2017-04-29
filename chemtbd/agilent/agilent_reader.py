from chemtbd import utils
from chemtbd.agilent.gcms_data import GcmsData
from chemtbd.agilent.gcms_result import GcmsResult

AGILENT_READERS = {
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
    'results.csv': GcmsResult
}


class Agilent(object):
    ''' read Agilent gcms files from provided directory

        Arguments: 
            dir_path: directory to agilent gcms files

        Attributes:
            raw: data extracted from data.ms as pd DataFrame
            results: data extracted from results.csv as pd DataFrame
    '''
    def __init__(self, dir_path):
        self.files = {fn.lower(): fp for fn, fp in utils.diriter(dir_path)}
        self._data = {fn.lower(): None for fn in self.files}

    def _data_cache(self, key):
        ''' load or return data associated with file key
        '''
        if key not in self._data:
            assert 'file does not exist in provided directory'

        if key not in AGILENT_READERS:
            assert 'file not supported'

        if not AGILENT_READERS[key]:
            assert 'file not supported'

        if self._data[key] is None:
            self._data[key] = AGILENT_READERS[key](self.files[key])
        return self._data[key]

    @property
    def raw(self):
        key = 'data.ms'
        return self._data_cache(key)

    @property
    def results(self):
        key = 'results.csv'
        return self._data_cache(key)


