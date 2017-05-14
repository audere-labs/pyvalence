import re
import csv
import numpy as np
import pandas as pd
from .gcms_base import GcmsIoBase

'''
    io for Agilent .D RESULTS.CSV file
'''

TIC_COLSTR = {
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

LIB_COLSTR = {
    'Header=': ('header=', 'O'),
    'PK': ('pk', 'i4'),
    'RT': ('rt', 'f4'),
    'Area Pct': ('pct_area', 'f4'),
    'Library/ID': ('library_id', 'O'),
    'Ref': ('ref', 'i4' ),
    'CAS': ('cas', 'O'),
    'Qual': ('qual', 'i4'),
}

FID_COLSTR = { 
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

COLSTR_KEY = {'tic': TIC_COLSTR, 'lib': LIB_COLSTR, 'fid': FID_COLSTR}


def reader(file_path):
    '''
        read Agilent RESULTS.csv into list of lists
        where each list item is the lines representing
        a tic, fid, or lib table
    '''
    def istablerow(line):
        ''' return true if line is table row '''
        return re.match('\d+=', line)

    def isheader(line):
        ''' return true if line is header '''
        return line[0] == 'Header='

    def seek_rows(header, gen):
        ''' gen is at position after header seek until
            no more table rows or stopiter exception
        '''
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
        ''' split csv generator into meta information
            and list of individual tables of tokens
        '''    
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


class GcmsResults(GcmsIoBase):
    ''' manages reading of Agilent RESULT.csv
        and mutation of tables into single pandas df
        
        Arguments:
            file_path: path to RESULTS.csv file

        Attributes:
            data: tic, lib, and fid tables as single DataFrame
            tic: tic columns from data
            lib: lib columns from data
            fid: fid columns from data

        Methods:
             __call__: returns data attribute
    '''
    def __init__(self, file_path):
        super().__init__(COLSTR_KEY, reader, file_path)

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
