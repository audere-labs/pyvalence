import numpy as np
import pandas as pd

'''
'''

def clean_name(item):
    ''' return clean name from colstr item '''
    return item[0]


def np_type(item):
    ''' return np type from clstr item '''
    return item[1]


def pd_columns(header, colstr):
    ''' return clean header column name
        specification in pd DataFrame
    '''
    return [clean_name(colstr[col]) for col in header]


def column_structure(header, keys):
    ''' determine table column structure from
        table header
    '''
    for key, val in keys.items():
        if set(header) == set(val.keys()):
            return key, val
    raise Exception(
        'data is jacked: {}'.format(header)
    )


class GcmsIoBase(object):
    '''
        Base Agilent gcms reader class
        
        Arguments:
            col_keys: dictionary containing table structure
        
        Methods:
            as_dataframe: returns input data transformed to pd DataFrame

    '''
    def __init__(self, col_keys):
        self.col_keys = col_keys
        self._data = None

    def as_dataframe(self, header, data):
        ''' transform list of rows as lists into
            pandas DataFrame with appropriate names and types
        '''
        key, colstr = column_structure(header, self.col_keys)
        return (pd.DataFrame(data, columns=pd_columns(header, colstr))
                .apply(pd.to_numeric, errors='ignore')
                .add_prefix('{}_'.format(key)))



    