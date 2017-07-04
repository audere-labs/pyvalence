""" Common build functionality for Agilent .D table files

        - RESULTS.CSV
        - DATA.MS
"""

import pandas as pd


def clean_name(item):
    """ return clean name from colstr item
    """
    return item[0]


def np_type(item):
    """ return np type from colstr item
    """
    return item[1]


def pd_columns(header, colstr):
    """ return clean column names for header
        specification in pd DataFrame
    """
    return [clean_name(colstr[col]) for col in header]


def column_structure(header, keys):
    """ determine table column structure from
        table header
    """
    for key, val in keys.items():
        if set(header) == set(val.keys()):
            return key, val
    raise Exception(
        # TODO: Formalize this exception
        'expected column structure: {}, found {}'.format(
            val.keys(), header)
    )


class GcmsBuildBase(object):
    """ Base Agilent gcms reader class

        Arguments:
            col_keys: dictionary containing table structure

        Methods:
            as_dataframe: returns input data transformed to pd DataFrame

    """
    def __init__(self, col_keys, reader, file_path):
        self.col_keys = col_keys
        self._meta, self._tables = reader(file_path)
        self._data = {}

    @property
    def source_data(self):
        """ lazily load data from file
        """
        if not self._data:
            self._data = self._build_data()
        return self._data

    def _as_dataframe(self, header, data):
        """ transform list of rows as lists of tokens into
            pandas DataFrame with appropriate names and types
        """
        key, colstr = column_structure(header, self.col_keys)
        return (key, (pd.DataFrame(data, columns=pd_columns(header, colstr))
                        .apply(pd.to_numeric, errors='ignore')))

    def _build_data(self):
        """ convert list of tables to dictionary of pandas dataframe
        """
        def build(tbl):
            return self._as_dataframe(tbl[0], tbl[1:])
        return {key: df for key, df in map(build, self._tables)}

    def _access(self, key):
        if key not in self.source_data:
            # raise AttributeError(
            #     '{} has no attribute {}'.format(type(self).__name__, key)
            # )
            return None
        return self._data[key]

    def __getitem__(self, key):
        ''' overload [] '''
        return self._access(key)
