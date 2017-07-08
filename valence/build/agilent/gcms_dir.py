""" Manages reading all files in Agilent GCMS .D directory
"""
from valence import utils
from .gcms_datams import GcmsDataMs
from .gcms_results import GcmsResults


FILE_STR = {
    'acqmeth.txt': None,
    'audit.txt': None,
    'cnorm.ini': None,
    'data.ms': GcmsDataMs,
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
    """ Read Agilent GCMS files from .D directory

        Arguments:
            dir_path (str): directory to agilent GCMS files

        Attributes:
            data (DataFrame): data extracted from data.ms
            results (DataFrame): data extracted from results.csv
    """
    def __init__(self, dir_path, file_str=FILE_STR):
        self.dir_path = dir_path
        self.file_str = file_str
        self.files = {fn.lower(): fp for fn, fp in utils.diriter(dir_path)}
        self._data = {fn.lower(): None for fn in self.files}

    def _data_cache(self, key):
        """ load and return data associated with file key
        """
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
        """ return data from DATA.MS
        """
        return self._data_cache('data.ms')

    @property
    def results(self):
        """ return data from RESULTS.CSV
        """
        return self._data_cache('results.csv')
