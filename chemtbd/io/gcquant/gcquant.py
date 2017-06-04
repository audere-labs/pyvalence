import os
import pandas as pd
from .gcquant_methods import GCMethods

class GCQuant(object):
    ''' quantifies the concentrations based on calibration curves using dataframes
        generated from Agilent

        Constructors:
            align: aligns lib and tic/fid on r.t.

        Attributes:
            keys: dir_keys
            datams: data collected from data.ms files as DataFrame
            results_fid: fid table from results.csv files as DataFrame
            resutls_lib: lib table from results.csv files as DataFrame
            results_tic: tic table from result.csv files as DataFrame
    '''

    def __init__(self, lib, area):
        self._align = self._matchlib2area(lib,area)

    @property
    def align(self):
        return self._align

